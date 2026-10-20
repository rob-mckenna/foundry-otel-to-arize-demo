"""Fixed-target GET/VFS proof; ZIP POST requires separate explicit authorization."""
import argparse
import datetime
import hashlib
import http.client
import io
import json
import os
from pathlib import Path
import re
import shutil
import socket
import ssl
import subprocess
import urllib.error
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parents[1]
SUB = "c81fda52-936e-4f14-8af4-951c0dbb92d2"
TENANT = "e500988a-f788-4f81-b1ba-e3ad7cd66171"
ARM = "https://management.azure.com"
SCM = "https://fotoa-demo-func-eastus2.scm.azurewebsites.net"
SITE = (f"/subscriptions/{SUB}/resourceGroups/fotoa-demo-rg/providers/"
        "Microsoft.Web/sites/fotoa-demo-func-eastus2")
DEPLOYMENTS = ARM + SITE + "/deployments?api-version=2023-12-01"
SOURCE_NAMES = (
    "function_app.py", "host.json", "requirements.txt",
    "telemetry_pipeline/__init__.py", "telemetry_pipeline/batch.py",
    "telemetry_pipeline/durable.py", "telemetry_pipeline/durable_runtime.py",
    "telemetry_pipeline/durable_store.py", "telemetry_pipeline/exporter.py",
    "telemetry_pipeline/function_app.py", "telemetry_pipeline/mapping.py",
    "telemetry_pipeline/strict_sender.py",
)
BASELINE_ID = "127794d4-c4a1-466f-b000-08ca0bec3bcb"
OLD_SOURCE_SHA = "c0938d860fd0f48ea5899b2ef8bc3354873e4d6e413d5d19a0db7ecb02432790"
FINAL_SHA = "16de4fdd0e951efa957d470d9e71822d5de558bcb3f16fb44522169a9bd40382"
ENV = dict(os.environ, AZURE_CONFIG_DIR=str(REPO / ".azure-config"),
           AZURE_EXTENSION_USE_DYNAMIC_INSTALL="no", AZURE_CORE_COLLECT_TELEMETRY="no")


class SafeFailure(Exception):
    def __init__(self, phase, code, **metadata):
        self.safe = {"phase": phase, "code": code, **metadata}
        super().__init__(json.dumps(self.safe))


def check(condition, code):
    if not condition:
        raise SafeFailure("local-gate", code)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def bearer():
    try:
        p = subprocess.run(
            [shutil.which("az"), "account", "get-access-token", "--subscription", SUB,
             "--resource", ARM, "--only-show-errors", "-o", "json"],
            capture_output=True, text=True, timeout=60, env=ENV)
    except (OSError, TypeError, subprocess.TimeoutExpired):
        raise SafeFailure("bearer", "CliInvocationOrTimeout") from None
    if p.returncode:
        if re.search(r"\b429\b|too many requests", p.stderr, re.IGNORECASE):
            raise SafeFailure("bearer", "TokenEndpointThrottled", httpStatus=429,
                              exit=p.returncode) from None
        codes = sorted(set(re.findall(
            r"\b(?:AADSTS[0-9]+|AuthorizationFailed|AuthenticationFailed|"
            r"InvalidAuthenticationTokenTenant|InteractionRequired|"
            r"CredentialUnavailableError)\b", p.stderr)))
        raise SafeFailure("bearer", "CliBearerAcquisitionFailed",
                          exit=p.returncode, identityCodes=codes[:4])
    try:
        auth = json.loads(p.stdout)
        check(auth["tenant"] == TENANT and auth["subscription"] == SUB, "BearerScopeMismatch")
        check(auth.get("tokenType") == "Bearer" and bool(auth.get("accessToken")), "BearerShapeMismatch")
        return auth["accessToken"]
    except (KeyError, ValueError):
        raise SafeFailure("bearer", "CliBearerDecodeFailed") from None


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def allowed_get(url):
    if url == DEPLOYMENTS:
        return True
    if url.startswith(SCM + "/api/deployments/"):
        return bool(re.fullmatch(r"[0-9a-f-]{36}", url.rsplit("/", 1)[1]))
    return url in {SCM + "/api/vfs/site/wwwroot/" + name
                   for name in (*SOURCE_NAMES, "telemetry_pipeline/source_policy.py")}


class Channel:
    def __init__(self, token):
        self.token = token
        self.opener = urllib.request.build_opener(NoRedirect)

    def request(self, url, phase, *, body=None, authorize_post=False, limit=1024 * 1024):
        if body is None:
            check(allowed_get(url), "GetPathNotAllowlisted")
        else:
            check(authorize_post and url == SCM + "/api/zipdeploy?isAsync=true",
                  "ZipPostNotAuthorized")
            check(digest(body) == FINAL_SHA, "ZipDigestMismatch")
        method = "GET" if body is None else "POST"
        headers = {"Authorization": "Bearer " + self.token}
        if body is not None:
            headers["Content-Type"] = "application/zip"
        request = urllib.request.Request(url, data=body, method=method, headers=headers)
        try:
            with self.opener.open(request, timeout=90) as response:
                data = response.read(limit + 1)
                if len(data) > limit:
                    raise SafeFailure(phase, "ResponseLimitExceeded", httpStatus=response.status)
                return response.status, data, response.headers
        except urllib.error.HTTPError as exc:
            category = {401: "BearerRejected", 403: "Forbidden", 404: "NotFound",
                        409: "Conflict", 429: "Throttled"}.get(
                            exc.code, "RedirectBlocked" if 300 <= exc.code < 400 else "HttpFailure")
            raise SafeFailure(phase, category, httpStatus=exc.code) from None
        except urllib.error.URLError as exc:
            reason = exc.reason
            if isinstance(reason, ssl.SSLCertVerificationError):
                raise SafeFailure(phase, "TLSCertificateVerificationFailed",
                                  verifyCode=reason.verify_code) from None
            if isinstance(reason, ssl.SSLError):
                raise SafeFailure(phase, "TLSHandshakeFailed") from None
            if isinstance(reason, socket.gaierror):
                raise SafeFailure(phase, "DNSResolutionFailed", errno=reason.errno) from None
            raise SafeFailure(phase, "TransportFailure", reasonType=type(reason).__name__) from None
        except TimeoutError:
            raise SafeFailure(phase, "TimeoutSubmissionUnknown" if body is not None else "GetTimeout") from None
        except (OSError, http.client.HTTPException) as exc:
            raise SafeFailure(phase, "ConnectionFailureSubmissionUnknown" if body is not None
                              else "ConnectionFailure", reasonType=type(exc).__name__) from None


def active(channel):
    _, data, _ = channel.request(DEPLOYMENTS, "arm-deployments")
    try:
        rows = json.loads(data)["value"]
        active_rows = [r for r in rows if r["properties"].get("active")]
        check(len(active_rows) == 1, "ActiveDeploymentNotUnique")
        r = active_rows[0]
        p = r["properties"]
        identity = r["name"].rsplit("/", 1)[-1]
        check(bool(re.fullmatch(r"[0-9a-f-]{36}", identity)), "DeploymentIdentityMalformed")
        return {"id": identity, "status": p.get("status"),
                "start": p.get("start_time"), "end": p.get("end_time")}
    except (KeyError, ValueError, TypeError):
        raise SafeFailure("arm-deployments", "MetadataDecodeFailed") from None


def candidate(mode):
    if mode == "baseline":
        archive = REPO / ".azure-sandbox/issue143-c0938d860fd0f48ea5899b2ef8bc3354873e4d6e413d5d19a0db7ecb02432790.zip"
        data = archive.read_bytes()
        check(digest(data) == OLD_SOURCE_SHA, "CandidateArchiveDigestMismatch")
        with zipfile.ZipFile(io.BytesIO(data)) as package:
            check(set(package.namelist()) == set(SOURCE_NAMES), "CandidateSourceInventoryMismatch")
            return {n: digest(package.read(n)) for n in SOURCE_NAMES}
    receipt = json.loads((ROOT / ".release/pipeline-health-final-a.receipt.json").read_text())
    check(receipt["packageSha256"] == FINAL_SHA, "FinalReceiptDigestMismatch")
    check(set(receipt["sourceSha256"]) == set(SOURCE_NAMES) | {"telemetry_pipeline/source_policy.py"},
          "FinalSourceInventoryMismatch")
    return receipt["sourceSha256"]


def proof(channel, mode):
    expected = candidate(mode)
    before = active(channel)
    if mode == "baseline":
        check(before["id"] == BASELINE_ID, "BaselineDeploymentChanged")
    _, body, _ = channel.request(SCM + "/api/deployments/" + before["id"], "scm-deployment")
    try:
        row = json.loads(body)
        scm = {k: row.get(k) for k in
               ("id", "status", "active", "complete", "start_time", "end_time")}
    except ValueError:
        raise SafeFailure("scm-deployment", "MetadataDecodeFailed") from None
    check(scm["id"] == before["id"] and scm["active"] is True
          and scm["complete"] is True and scm["status"] == 4, "ScmDeploymentIdentityMismatch")
    hashes = {}
    failures = {}
    for name in expected:
        try:
            _, data, _ = channel.request(SCM + "/api/vfs/site/wwwroot/" + name, "vfs:" + name)
            hashes[name] = digest(data)
        except SafeFailure as exc:
            if exc.safe.get("httpStatus") != 404:
                raise
            # Missing allowlisted files are evidence, not a reason to explore.
            failures[name] = exc.safe
    after = active(channel)
    check(before == after, "DeploymentChangedDuringReadback")
    matches = {n: hashes.get(n) == expected[n] for n in expected}
    return {"mode": mode, "observedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "armDeploymentBefore": before, "armDeploymentAfter": after, "scmDeployment": scm,
            "sourceSha256": hashes, "candidateSha256": expected, "matches": matches,
            "fileFailures": failures,
            "allSourceBytesMatch": all(matches.values()), "httpGetCount": len(expected) + 3,
            "postCount": 0, "dependencyBytesVerified": False,
            "limit": "SCM-visible site/wwwroot only; not validated as the worker-mounted script root, package, memory or dependencies."}


def publish_once(channel, authorize_post):
    # Never called by baseline/readback. Future parent authorization is mandatory.
    check(authorize_post, "ZipPostNotAuthorized")
    data = (ROOT / ".release/pipeline-health-final-a.zip").read_bytes()
    check(digest(data) == FINAL_SHA, "ZipDigestMismatch")
    claim = ROOT / ".release/scm-zip-submission-intent.json"
    check(not claim.exists(), "ExistingSubmissionReconcileGetOnly")
    with claim.open("x") as stream:
        json.dump({"packageSha256": FINAL_SHA, "singleAttempt": True}, stream)
    # No retry on timeout/failure; the durable intent forces GET-only reconciliation.
    status, _, headers = channel.request(SCM + "/api/zipdeploy?isAsync=true", "zip-post",
                                        body=data, authorize_post=True)
    location = headers.get("Location", "")
    match = re.search(r"/api/deployments/([0-9a-f-]{36})(?:[/?]|$)", location)
    return {"httpStatus": status, "deploymentId": match[1] if match else None,
            "packageSha256": FINAL_SHA, "postCount": 1,
            "nextAction": "GET-only status reconciliation and explicit readback; never repeat POST."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("baseline", "readback", "publish"), default="baseline")
    parser.add_argument("--authorize-zip-post", action="store_true",
                        help="Use ONLY after separate parent cloud-write authorization.")
    parser.add_argument("--evidence-name",
                        help="Optional immutable .release JSON stem for a distinct bounded read.")
    args = parser.parse_args()
    if args.mode != "publish":
        check(not args.authorize_zip_post, "PostAuthorizationNotNeededForGet")
    else:
        check(args.authorize_zip_post, "ZipPostNotAuthorized")
    stem = args.evidence_name or ("scm-" + args.mode + "-proof")
    check(bool(re.fullmatch(r"scm-[a-z0-9-]{1,64}", stem)), "EvidenceNameNotSafe")
    output = ROOT / ".release" / (stem + ".json")
    check(not output.exists(), "ImmutableProofAlreadyExists")
    result = {}
    try:
        channel = Channel(bearer())
        result = (publish_once(channel, args.authorize_zip_post) if args.mode == "publish"
                  else proof(channel, args.mode))
    except SafeFailure as exc:
        result = {"mode": args.mode, "status": "FAILED", "diagnostic": exc.safe,
                  "noAutomaticRetry": True}
    finally:
        output.parent.mkdir(exist_ok=True)
        with output.open("x") as stream:
            json.dump(result, stream, indent=2)
            stream.write("\n")
    print(json.dumps(result))
    if result.get("status") == "FAILED" or result.get("allSourceBytesMatch") is False:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
