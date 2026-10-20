"""Five-check transport adapter for the pinned official helper, not an executor.

Only az version/account show/bicep build and subscription validate/what-if are
allowed. Provider responses are projected; raw failure bodies stay in memory.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

WORKTREE = Path(__file__).resolve().parents[2]
TEAM_ROOT = WORKTREE.parents[1]
SUB = "c81fda52-936e-4f14-8af4-951c0dbb92d2"
HELPER = TEAM_ROOT / ".azure-sandbox/issue147-workflow/qa-followup-20261019/azure-validate/references/recipes/scripts/validate-deployment.ps1"
HELPER_HASH = "ac49678e5941f2946d8b216370e30dbd8b3451cb15652f8042bb9fad77bcb9bb"
TEMPLATE = WORKTREE / "infra/issue147-first-allocation.bicep"
COMPILED = WORKTREE / ".azure/issue147-first-allocation.compiled.json"
PROFILE = WORKTREE / "infra/main.issue147-existing-network.parameters.json"
CHECKS = ("cli", "authentication", "compile", "validate", "what-if")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def redact(text):
    text = re.sub(r"-----BEGIN [^-]*PRIVATE KEY-----.*?(?:-----END [^-]*PRIVATE KEY-----|$)",
                  "[REDACTED PRIVATE KEY]", text, flags=re.S)
    text = re.sub(r"(?i)(?:https?|postgres(?:ql)?|mongodb|mysql)://[^\s\"'<>]+", "[REDACTED URL]", text)
    text = re.sub(r"eyJ[\w-]+\.[\w-]+\.[\w-]+", "[REDACTED JWT]", text)
    text = re.sub(r"(?i)\b(?:Bearer\s+\S+|(?:sk-|gh[pousr]_|github_pat_)[A-Za-z0-9_-]+|AKIA[A-Z0-9]{16})",
                  "[REDACTED CREDENTIAL]", text)
    sensitive_name = r"\b(?:[A-Za-z_]*(?:password|passwd|pwd|secret|token|api[-_]?key|accountkey|sharedaccesskey|sharedaccesssignature|connectionstring|instrumentationkey)[A-Za-z_]*|key|sig|sas|authorization|credential)"
    text = re.sub(sensitive_name + r"""["']?\s*[:=]\s*(?:"[^"]*"|'[^']*')""",
                  "[REDACTED ASSIGNMENT]", text, flags=re.I)
    text = re.sub(sensitive_name + r"""["']?\s*[:=]\s*[^;\s,"'}]+""",
                  "[REDACTED ASSIGNMENT]", text, flags=re.I)
    text = re.sub(r"(?i)\b(?:AccountName|EndpointSuffix|Server|Host|Database)\s*=[^;\s]+",
                  "[REDACTED CONNECTION FIELD]", text)
    text = re.sub(r"[A-Za-z0-9_+/=-]{48,}", "[REDACTED OPAQUE VALUE]", text)
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[REDACTED EMAIL]", text)
    return text


def failure_diagnostic(raw):
    """Keep actionable ARM text, not arbitrary response objects/properties."""
    codes, messages, correlations = [], [], []
    def visit(value):
        if isinstance(value, dict):
            code = value.get("code")
            if isinstance(code, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,100}", code):
                codes.append(code)
            if isinstance(value.get("message"), str):
                messages.append(value["message"])
            correlation = value.get("correlationId")
            if isinstance(correlation, str) and re.fullmatch(r"[a-fA-F0-9-]{36}", correlation):
                correlations.append(correlation)
            for key in ("error", "details", "innererror", "innerError"):
                if key in value:
                    visit(value[key])
        elif isinstance(value, list):
            for item in value:
                visit(item)
    try:
        visit(json.loads(raw.removeprefix("ERROR: ").strip()))
    except ValueError:
        start = raw.find("{")
        if start >= 0:
            try:
                visit(json.JSONDecoder().raw_decode(raw[start:])[0])
            except ValueError:
                pass
    if not messages:
        # CLI often emits plain "ERROR: InvalidTemplate - ...", not JSON.
        messages = [re.sub(r"(?s)\{.*", "[unparsed structured body suppressed]", raw)]
    for code in re.findall(r"(?:\bCode:\s*|\bERROR:\s*\(?|\()([A-Z][A-Za-z0-9_.]+)(?=\)|\s*[-:])", raw):
        codes.append(code)
    correlations += re.findall(r"(?i)correlation(?:\s*id|Id)[\"'\s:=]+([a-f0-9-]{36})", raw)
    diagnostic = redact(" | ".join(messages))
    # Do not persist raw JSON resource properties embedded in a message.
    diagnostic = re.sub(r'(?is)["\']?properties["\']?\s*:\s*\{.*', "properties: [REDACTED]", diagnostic)
    return {"errorCodes": sorted(set(codes)), "correlationIds": sorted(set(correlations)),
            "diagnostic": diagnostic[:1600].strip()}


def identify(args):
    if args[:1] == ["version"]:
        return "cli"
    if args[:2] == ["account", "show"]:
        return "authentication"
    if args[:2] == ["bicep", "build"]:
        return "compile"
    if args[:3] == ["deployment", "sub", "validate"]:
        return "validate"
    if args[:3] == ["deployment", "sub", "what-if"]:
        return "what-if"
    raise ValueError("Only the pinned helper's five analysis checks are allowed")


def command(check):
    common = ["--subscription", SUB, "--only-show-errors", "-o", "json"]
    if check == "cli":
        return ["version", *common]
    if check == "authentication":
        return ["account", "show", "--query", "{id:id,state:state}", *common]
    if check == "compile":
        return ["bicep", "build", "--file", str(TEMPLATE), "--outfile", str(COMPILED), *common]
    base = ["deployment", "sub", check, "--location", "eastus2", "--name", "issue147-vault-graph-analysis",
            "--template-file", str(COMPILED), "--validation-level", "Provider", *common]
    if check == "validate":
        return [*base, "--query", "{status:properties.provisioningState,correlationId:properties.correlationId,errorCode:error.code}"]
    return [*base, "--result-format", "ResourceIdOnly", "--no-pretty-print", "--no-prompt",
            "--query", "{status:status,correlationId:correlationId,changes:changes[].{resourceId:resourceId,changeType:changeType},errorCode:error.code}"]


def run_check(check, receipt_directory, runner=subprocess.run):
    if sha(HELPER) != HELPER_HASH:
        raise ValueError("Pinned official helper hash mismatch")
    receipt_directory = receipt_directory.resolve()
    if not receipt_directory.is_relative_to(WORKTREE / ".azure"):
        raise ValueError("Receipts must remain inside worktree .azure")
    receipt_directory.mkdir(parents=True, exist_ok=True)
    path = receipt_directory / f"{CHECKS.index(check) + 1}-{check}.json"
    if path.exists():
        raise ValueError("Immutable receipt already exists; no overwrite")
    # A failed auth/build/provider step ends analysis, rather than falling back.
    previous = [receipt_directory / f"{i + 1}-{name}.json" for i, name in enumerate(CHECKS[:CHECKS.index(check)])]
    if any(not p.exists() or json.loads(p.read_text())["exitCode"] != 0 for p in previous):
        raise ValueError("Prior check failed or missing; stop analysis")
    args = [shutil.which("az") or "az", *command(check)]
    receipt = {"check": check, "startedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "command": args, "azureConfigDirectory": str(TEAM_ROOT / ".azure-config"),
               "officialHelperSha256": HELPER_HASH, "profileSha256": sha(PROFILE),
               "adapterSha256": sha(Path(__file__)),
               "invocationAdapterSha256": sha(Path(__file__).with_name("invoke-issue147-official-validation.ps1")),
               "wrapperSourceSha256": sha(TEMPLATE)}
    if COMPILED.exists():
        receipt["templateSha256Before"] = sha(COMPILED)
    try:
        result = runner(args, env=dict(os.environ, AZURE_CONFIG_DIR=str(TEAM_ROOT / ".azure-config"),
                                      AZURE_LOGGING_ENABLE_LOG_FILE="false", AZURE_CORE_COLLECT_TELEMETRY="no"),
                        capture_output=True, text=True, timeout=600, check=False)
        receipt["exitCode"] = result.returncode
        if result.returncode:
            receipt.update(failure_diagnostic(result.stderr + "\n" + result.stdout))
        else:
            data = json.loads(result.stdout) if result.stdout.strip() else {}
            if check == "cli":
                receipt["cliVersion"] = data["azure-cli"]
            elif check == "authentication":
                if data != {"id": SUB, "state": "Enabled"}:
                    raise ValueError("Exact subscription is not Enabled")
                receipt["result"] = data
            elif check == "compile":
                receipt["compiledTemplateSha256"] = sha(COMPILED)
            else:
                receipt["result"] = {key: data.get(key) for key in ("status", "correlationId", "errorCode")}
                if data.get("status") != "Succeeded" or data.get("errorCode"):
                    raise ValueError("Provider analysis did not return Succeeded without errors")
                if check == "what-if":
                    changes = [{"resourceId": row["resourceId"], "changeType": row["changeType"]}
                               for row in data.get("changes", [])]
                    receipt["result"]["changes"] = changes
                    receipt["changeCounts"] = {kind: sum(row["changeType"] == kind for row in changes)
                                               for kind in ("Create", "Modify", "Delete", "Unsupported", "Ignore", "NoChange")}
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError) as error:
        receipt["exitCode"] = 1
        receipt["errorCodes"] = [type(error).__name__]
        receipt["diagnostic"] = redact(str(error))[:1600] if not isinstance(error, subprocess.TimeoutExpired) else "CLI analysis timed out; no fallback"
    receipt["completedUtc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if COMPILED.exists():
        receipt["templateSha256"] = sha(COMPILED)
    with path.open("x", encoding="utf-8") as target:
        json.dump(receipt, target, indent=2)
        target.write("\n")
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipts", type=Path, required=True)
    parser.add_argument("helper_args", nargs=argparse.REMAINDER)
    parsed = parser.parse_args()
    try:
        args = parsed.helper_args
        if args[:1] == ["--"]:
            args = args[1:]
        receipt = run_check(identify(args), parsed.receipts)
        if receipt["exitCode"]:
            print(json.dumps({k: receipt.get(k) for k in ("errorCodes", "correlationIds", "diagnostic")}))
        elif receipt["check"] == "authentication":
            print(SUB)
        elif receipt["check"] == "what-if":
            symbols = {"Create": "+", "Modify": "~", "Delete": "-"}
            for row in receipt["result"]["changes"]:
                print(f"{symbols.get(row['changeType'], '=')} {row['resourceId']} [{row['changeType']}]")
        return receipt["exitCode"]
    except (ValueError, OSError) as error:
        print(redact(str(error))[:1600])
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
