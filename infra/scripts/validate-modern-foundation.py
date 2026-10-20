"""Offline prepared-profile gate. No Azure SDK, subprocess, auth or secret reads.

Reads only the explicit ARM parameter file supplied by the operator. Secret
material is forbidden: tracing accepts only a version-pinned deployment reference.
Examples deliberately fail; this validates configuration, not Azure availability.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
from pathlib import Path
import re
import sys

ZONES = {
    "cognitiveServices": "privatelink.cognitiveservices.azure.com",
    "openAI": "privatelink.openai.azure.com",
    "servicesAI": "privatelink.services.ai.azure.com",
    "vault": "privatelink.vaultcore.azure.net",
    "blob": "privatelink.blob.core.windows.net",
    "queue": "privatelink.queue.core.windows.net",
    "table": "privatelink.table.core.windows.net",
}
RESOURCE_PREFIX = r"/subscriptions/[0-9a-f-]{36}/resourceGroups/[^/]+/providers/"
SUBNET = RESOURCE_PREFIX + r"Microsoft\.Network/virtualNetworks/[^/]+/subnets/[^/]+"
VAULT = RESOURCE_PREFIX + r"Microsoft\.KeyVault/vaults/[a-z0-9-]+"
REQUIRED = (
    "projectToken", "environment", "location", "regionToken", "ownerTag", "costCenterTag",
    "accountName", "projectName", "customSubDomainName", "modelDeploymentName", "modelFormat",
    "modelName", "modelVersion", "modelDeploymentSkuName", "modelDeploymentCapacity",
    "modelVersionUpgradeOption", "modelDataResidencyApproval", "modelDeploymentApproved",
    "network", "functionPackageBlobName", "functionMaximumInstances", "arizeProjectName", "appInsightsConnectionName",
)


def validate_profile(document: dict) -> dict:
    parameters = document.get("parameters", {})
    if not isinstance(parameters, dict):
        raise ValueError("parameters must be an object")
    for name in REQUIRED:
        if name not in parameters or set(parameters[name]) != {"value"}:
            raise ValueError(f"Required nonsecret value missing: {name}")
    values = {k: v.get("value") for k, v in parameters.items()
              if isinstance(v, dict) and "value" in v}
    # Never echo values or raw JSON in diagnostics.
    text = json.dumps(parameters)
    if re.search(r"REPLACE_ME|YOUR_|00000000-0000-0000-0000-000000000000|<[^>]+>", text, re.I):
        raise ValueError("Non-executable example/placeholders must be replaced by approved inputs")
    for name in REQUIRED:
        if isinstance(values[name], str) and not values[name].strip():
            raise ValueError(f"Nonempty input required: {name}")
    if values["environment"] not in {"dev", "demo", "prod"}:
        raise ValueError("Invalid environment")
    if not re.fullmatch(r"[a-z0-9]{2,10}", values["projectToken"]):
        raise ValueError("Invalid projectToken")
    if not re.fullmatch(r"[a-z0-9]+", values["regionToken"]):
        raise ValueError("Invalid regionToken")
    for token, limit in [("kv", 24), ("st", 24), ("func", 60), ("ehns", 50)]:
        name = f'{values["projectToken"]}-{values["environment"]}-{token}-{values["regionToken"]}'
        if len(name.replace("-", "") if token == "st" else name) > limit:
            raise ValueError(f"Generated {token} name exceeds provider limit")
    for key in ("accountName", "projectName"):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{1,63}", values[key]):
            raise ValueError(f"Invalid {key}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}[a-z0-9]", values["customSubDomainName"]):
        raise ValueError("Invalid customSubDomainName")
    capacity = values["modelDeploymentCapacity"]
    if type(capacity) is not int or capacity < 1:
        raise ValueError("Positive explicit modelDeploymentCapacity required")
    if values["modelDeploymentApproved"] is not True:
        raise ValueError("Owner model/quota/cost approval required")
    if values["modelVersionUpgradeOption"] not in {
        "NoAutoUpgrade", "OnceCurrentVersionExpired", "OnceNewDefaultVersionAvailable",
    }:
        raise ValueError("Explicit supported modelVersionUpgradeOption required")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*\.zip", values["functionPackageBlobName"]):
        raise ValueError("functionPackageBlobName must be an immutable ZIP name, not a URL/SAS/path")
    if type(values["functionMaximumInstances"]) is not int or values["functionMaximumInstances"] != 1:
        raise ValueError("Fresh EP1 validation profile requires explicit functionMaximumInstances=1")
    if not 3 <= len(values["appInsightsConnectionName"]) <= 33:
        raise ValueError("appInsightsConnectionName must have 3-33 characters")
    network = values["network"]
    if not isinstance(network, dict):
        raise ValueError("network must be a typed ownership object")
    if network.get("mode") == "fresh":
        expected = {"mode", "virtualNetworkAddressPrefix", "privateEndpointSubnetAddressPrefix",
                    "functionIntegrationSubnetAddressPrefix"}
        if set(network) != expected:
            raise ValueError("Fresh network needs exactly three explicit CIDRs")
        try:
            vnet, pe, integration = [ipaddress.ip_network(network[k]) for k in (
                "virtualNetworkAddressPrefix", "privateEndpointSubnetAddressPrefix",
                "functionIntegrationSubnetAddressPrefix")]
            if not all(n.version == 4 for n in (vnet, pe, integration)):
                raise ValueError
            if not pe.subnet_of(vnet) or not integration.subnet_of(vnet) or pe.overlaps(integration):
                raise ValueError
            if integration.prefixlen > 26:
                raise ValueError
        except ValueError:
            raise ValueError("CIDRs must be disjoint IPv4 subnets inside VNet; integration at least /26") from None
    elif network.get("mode") == "existing":
        expected = {"mode", "privateEndpointSubnetResourceId", "functionIntegrationSubnetResourceId",
                    "privateDnsZoneIds", "dnsLinksManagedExternally"}
        if set(network) != expected or network["dnsLinksManagedExternally"] is not True:
            raise ValueError("Existing topology requires explicit external DNS-link ownership")
        pe = network["privateEndpointSubnetResourceId"]
        integration = network["functionIntegrationSubnetResourceId"]
        if not all(re.fullmatch(SUBNET, x, re.I) for x in (pe, integration)):
            raise ValueError("Exact subnet ARM IDs required")
        if pe.lower() == integration.lower() or pe.rsplit("/", 1)[0].lower() != integration.rsplit("/", 1)[0].lower():
            raise ValueError("Distinct PE/integration subnets in one approved VNet required")
        zones = network["privateDnsZoneIds"]
        if not isinstance(zones, dict) or set(zones) != set(ZONES):
            raise ValueError("All seven exact DNS zone IDs required")
        for key, zone in ZONES.items():
            if not re.fullmatch(RESOURCE_PREFIX + r"Microsoft\.Network/privateDnsZones/" + re.escape(zone),
                                zones[key], re.I):
                raise ValueError(f"Incorrect private DNS zone ID: {key}")
    else:
        raise ValueError("network mode must be fresh or existing; no public mode")
    mode = values.get("tracingAssociationMode", "preserveExisting")
    if mode not in {"preserveExisting", "ApiKey"}:
        raise ValueError("Fresh tracing supports preserveExisting or separately approved ApiKey only")
    secret = parameters.get("appInsightsConnectionString")
    if secret is not None:
        reference = secret.get("reference", {})
        if (set(secret) != {"reference"} or
                set(reference) != {"keyVault", "secretName", "secretVersion"} or
                set(reference.get("keyVault", {})) != {"id"} or
                not re.fullmatch(VAULT, reference.get("keyVault", {}).get("id", ""), re.I) or
                not re.fullmatch(r"[A-Za-z0-9-]+", reference.get("secretName", "")) or
                not re.fullmatch(r"[a-f0-9]{32}", reference.get("secretVersion", ""), re.I)):
            raise ValueError("Tracing accepts only immutable Key Vault deployment reference; plaintext forbidden")
    if mode == "ApiKey" and (secret is None or values.get("appInsightsConnectionPropertiesReviewed") is not True):
        raise ValueError("Active tracing needs reviewed properties and pinned vault reference")
    return {"offlineProfileValid": True, "tracingPutRequested": mode == "ApiKey",
            "providerValidated": False, "privateRuntimeVerified": False, "consumerEnabled": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parameters", type=Path, required=True)
    args = parser.parse_args()
    # Limit this utility to explicit ARM JSON parameter profiles, not settings/env.
    if args.parameters.suffix.lower() != ".json" or "parameters" not in args.parameters.name.lower():
        parser.error("Only an explicit *.parameters*.json ARM profile is accepted")
    try:
        print(json.dumps(validate_profile(json.loads(args.parameters.read_text(encoding="utf-8")))))
        return 0
    except (ValueError, KeyError, TypeError, OSError):
        # Suppress payload and unexpected raw exceptions, including any operator input.
        print("Offline profile rejected: missing, placeholder, invalid or unapproved input; no Azure action.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
