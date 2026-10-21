"""Offline attachment-contract checks. No Azure calls, writes, or runtime attestation."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import uuid


ROOT = Path(__file__).resolve().parents[2]
REQUIRED_EVIDENCE = {
    "exactAgentVersionExists",
    "agentComponentWorkspaceLink",
    "completeSettingsAndExportSnapshot",
    "privatePremiumFunctionAndSystemIdentity",
    "privateHostStorageAndPackageAccess",
    "privateKeyVaultReferencesResolved",
    "eventHubIdentityAndExportAccess",
    "separateHealthSinkWithoutExport",
    "scopedRbacReady",
    "privatePublicationAndDnsReady",
    "linuxPackageAndRuntimeSetAttested",
}
PARAMETERS = {
    "existingAgent", "functionAppName", "functionPrincipalId", "storageAccountName",
    "workspaceName", "workspaceCustomerId", "agentComponentResourceId", "functionHealthComponentResourceId",
    "functionHealthWorkspaceResourceId", "keyVaultName",
    "functionHealthConnectionStringSecretName", "arizeEndpointSecretName",
    "arizeSpaceSecretName", "arizeApiKeySecretName", "arizeProjectName",
    "eventHubNamespaceName", "eventHubName", "eventHubConsumerGroupName",
    "exportRuleName", "existingExportTableNames", "existingExportEnabled",
    "existingFunctionAppSettings",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def local_json(path):
    require(not any(p == ".env" or p.startswith(".env.") for p in Path(path).parts),
            "secret configuration files are not inputs")
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT), "inputs must remain inside this worktree")
    require(not any(p == ".env" or p.startswith(".env.") for p in path.parts),
            "secret configuration files are not inputs")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def resource_id(value, provider_type):
    return isinstance(value, str) and re.fullmatch(
        r"/subscriptions/[0-9a-fA-F-]{36}/resourceGroups/[^/]+/providers/"
        + re.escape(provider_type) + r"/[^/]+", value, re.IGNORECASE)


def validate(document):
    raw = document["parameters"]
    require(set(raw) == PARAMETERS, "parameter names must match the single attachment contract")
    require(all(isinstance(v, dict) and set(v) == {"value"} for v in raw.values()),
            "use explicit nonsecret parameter values, not deployment-time secret inputs")
    p = {key: item["value"] for key, item in raw.items()}
    for key in PARAMETERS - {"existingAgent", "existingFunctionAppSettings",
                             "existingExportTableNames", "existingExportEnabled"}:
        require(isinstance(p[key], str) and bool(p[key].strip())
                and p[key] == p[key].strip(), f"{key} must be a nonempty exact string")
    uuid.UUID(p["functionPrincipalId"])
    require(re.fullmatch(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}",
                         p["workspaceCustomerId"]),
            "workspaceCustomerId must be the LAW customerId UUID, not an ARM resource ID")
    require(re.fullmatch(r"[a-z0-9]{3,24}", p["storageAccountName"]),
            "storageAccountName must be a valid existing account name")
    require(re.fullmatch(r"[a-zA-Z][a-zA-Z0-9-]{1,22}[a-zA-Z0-9]", p["keyVaultName"]),
            "keyVaultName must be a vault name, not a URL or credential")
    for key in ("functionHealthConnectionStringSecretName", "arizeEndpointSecretName",
                "arizeSpaceSecretName", "arizeApiKeySecretName"):
        require(re.fullmatch(r"[a-zA-Z0-9-]{1,127}", p[key]), f"{key} must be a secret name only")
    require(type(p["existingExportEnabled"]) is bool, "preserve the reviewed export enabled state")
    tables = p["existingExportTableNames"]
    require(isinstance(tables, list) and tables and all(
        isinstance(t, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", t) for t in tables),
        "preserve the complete reviewed export table list")
    for key, kind in (
        ("agentComponentResourceId", "Microsoft.Insights/components"),
        ("functionHealthComponentResourceId", "Microsoft.Insights/components"),
        ("functionHealthWorkspaceResourceId", "Microsoft.OperationalInsights/workspaces"),
    ):
        require(resource_id(p[key], kind), f"{key} must be an ARM resource ID")
    agent_scope = p["agentComponentResourceId"].split("/providers/")[0]
    for key in ("functionHealthComponentResourceId", "functionHealthWorkspaceResourceId"):
        require(p[key].split("/providers/")[0].lower() == agent_scope.lower(),
                "all attachment resources must be in the same subscription/resource group")
    agent_workspace = agent_scope + "/providers/Microsoft.OperationalInsights/workspaces/" + p["workspaceName"]
    require(p["functionHealthComponentResourceId"].lower() != p["agentComponentResourceId"].lower()
            and p["functionHealthWorkspaceResourceId"].lower() != agent_workspace.lower(),
            "health component AND workspace must be separate from the exported agent sink")
    target = p["existingAgent"]
    require(isinstance(target, dict) and set(target) == {
        "accountResourceId", "projectResourceId", "modelDeploymentName", "agentName", "agentVersion"
    }, "existingAgent must describe the exact existing invocation target")
    require(resource_id(target["accountResourceId"], "Microsoft.CognitiveServices/accounts")
            and target["projectResourceId"].startswith(target["accountResourceId"] + "/projects/")
            and "/" not in target["projectResourceId"].split("/projects/", 1)[1],
            "project must be under the existing Foundry account")
    require(all(isinstance(target[k], str) and target[k].strip()
                for k in ("modelDeploymentName", "agentName", "agentVersion"))
            and re.fullmatch(r"[1-9][0-9]*", target["agentVersion"]),
            "record an exact numbered agent version; latest/unversioned is forbidden")
    settings = p["existingFunctionAppSettings"]
    require(isinstance(settings, dict) and all(
        isinstance(k, str) and isinstance(v, str) for k, v in settings.items()),
        "complete existing settings must be a string map")
    require(not any(k in settings for k in (
        "AzureWebJobsStorage", "EventHubConnection", "DURABLE_GENAI_ENABLED")),
        "remove legacy connection-string/direct-mode settings in a separately reviewed baseline")
    expected = {
        "AzureWebJobsStorage__accountName": p["storageAccountName"],
        "AzureWebJobsStorage__credential": "managedidentity",
        "WEBSITE_RUN_FROM_PACKAGE_BLOB_MI_RESOURCE_ID": "SystemAssigned",
    }
    require(all(settings.get(k) == v for k, v in expected.items()),
            "existing host/package storage must use this account and system identity")
    for suffix in ("blob", "queue", "table"):
        key = f"AzureWebJobsStorage__{suffix}ServiceUri"
        require(key not in settings or settings[key] ==
                f"https://{p['storageAccountName']}.{suffix}.core.windows.net",
                "explicit host storage URI must match the attested account")
    package_url = settings.get("WEBSITE_RUN_FROM_PACKAGE", "")
    require(re.fullmatch(
        rf"https://{p['storageAccountName']}\.blob\.core\.windows\.net/function-packages/[a-f0-9]{{64}}\.zip",
        package_url), "require an immutable SHA-named private Blob package URL without SAS")
    require("AZURE_CLIENT_ID" not in settings
            and not any(k.lower().endswith("__clientid") for k in settings),
            "this attachment supports system-assigned identity only")
    for key, value in settings.items():
        if re.search(r"KEY|TOKEN|PASSWORD|SECRET|CONNECTION_STRING|CONNECTIONSTRING", key, re.I):
            require(re.fullmatch(r"@Microsoft.KeyVault\(SecretUri=https://[a-zA-Z0-9-]+"
                                 r"\.vault\.azure\.net/secrets/[a-zA-Z0-9-]+/(?:[a-zA-Z0-9]+)?\)", value),
                    "sensitive existing settings must be Key Vault references")
    for key in ("PIPELINE_EXCLUDED_SERVICE_NAMES", "PIPELINE_EXCLUDED_COMPONENT_RESOURCE_IDS"):
        values = json.loads(settings.get(key, "[]"))
        require(isinstance(values, list) and all(
            isinstance(v, str) and v.strip() and v == v.strip() for v in values),
            f"{key} must be a JSON string array")
    return p


def validate_attestation(document, parameters):
    require(set(document) == {"parametersSha256", "confirmations"},
            "attestation requires parametersSha256 and confirmations only")
    digest = hashlib.sha256(json.dumps(parameters, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    require(document["parametersSha256"] == digest, "attestation does not bind these exact parameter values")
    confirmations = document["confirmations"]
    require(isinstance(confirmations, dict) and set(confirmations) == REQUIRED_EVIDENCE
            and all(v is True for v in confirmations.values()),
            "owner evidence incomplete; do not deploy, publish or activate")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parameters", required=True)
    parser.add_argument("--attestation", help="Optional owner evidence, not produced or verified by this checker")
    args = parser.parse_args()
    p = validate(local_json(args.parameters))
    if args.attestation:
        validate_attestation(local_json(args.attestation), p)
    digest = hashlib.sha256(json.dumps(p, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    print(json.dumps({
        "contract": "PASS", "parametersSha256": digest,
        "ownerConfirmationsPresent": bool(args.attestation),
        "liveReadiness": "NOT VERIFIED; offline checks never attest resources, package, or runtime",
        "requiredConfirmations": sorted(REQUIRED_EVIDENCE),
    }, indent=2))


if __name__ == "__main__":
    main()
