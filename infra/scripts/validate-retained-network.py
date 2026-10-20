"""Offline evidence/approval-packet consistency checks; never authorizes or deletes."""

import argparse
import hashlib
import json
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def rows(evidence, name):
    data = evidence[name]["data"]
    require(not data.get("nextLink"), f"Incomplete {name}")
    return data["items"]


def by_id(items):
    result = {item["id"].lower(): item for item in items}
    require(len(result) == len(items), "Duplicate IDs")
    return result


def validate(evidence, plan):
    require(evidence["subscriptionId"] == plan["subscriptionId"], "Subscription drift")
    require(evidence["resourceGroupId"] == plan["resourceGroupId"], "RG drift")
    require(plan["status"] == "AWAITING_EXPLICIT_OWNER_CONFIRMATION_NO_EXECUTION",
            "Packet is not an execution authorization")
    for name in ("explicitNicDeleteIds", "dnsRecordDeleteIds", "dnsZoneDeleteIds",
                 "roleDeleteIds", "otherExplicitDeleteIds"):
        require(plan[name] == [], f"Forbidden scope expansion: {name}")
    require(len(set(plan["explicitDeleteIdsInOrder"])) == 2, "Expected two exact PEs")
    endpoints = by_id(rows(evidence, "endpoints"))
    nics = by_id(rows(evidence, "nics"))
    resources = by_id(rows(evidence, "resources"))
    roles = rows(evidence, "roles")
    for index, pe_id in enumerate(plan["explicitDeleteIdsInOrder"]):
        pe = endpoints[pe_id.lower()]
        require(pe["type"].lower() == "microsoft.network/privateendpoints", "Wrong type")
        require(pe["managedBy"] is None and pe["state"] == "Succeeded", "PE drift")
        require(len(pe["connections"]) == 1 and not pe["manual"], "Connection drift")
        connection = pe["connections"][0]
        require(connection["status"] == "Disconnected", "PE is not disconnected")
        require(connection["groups"] == ["amlworkspace"], "Target group drift")
        environment = ("demo", "dev")[index]
        require(connection["target"] == (
            plan["resourceGroupId"] + "/providers/Microsoft.MachineLearningServices/"
            f"workspaces/fotoa-{environment}-aihub-eastus2"), "Target ID drift")
        require(connection["target"].lower() not in resources, "Hub still present")
        require(connection["id"] == plan["automaticConnectionRemovalIdsInOrder"][index],
                "Connection ID drift")
        nic_id = plan["automaticNicRemovalIdsInOrder"][index]
        require(pe["nics"] == [nic_id], "NIC link drift")
        nic = nics[nic_id.lower()]
        require(nic["managedBy"] == pe_id and nic["privateEndpointId"] == pe_id,
                "NIC ownership drift")
        require(not nic["virtualMachineId"] and not nic["nsgId"], "NIC attachment drift")
        require(len(nic["ipConfigurations"]) == 4, "IP configuration drift")
        for ip in nic["ipConfigurations"]:
            require(ip["subnetId"] == pe["subnetId"], "Subnet drift")
            require(not any(ip[key] for key in (
                "publicIPAddressId", "loadBalancerBackendAddressPools",
                "loadBalancerInboundNatRules", "applicationGatewayBackendAddressPools",
                "applicationSecurityGroups")), "Additional NIC consumer")
        require(sum(nic_id in item["nics"] for item in endpoints.values()) == 1,
                "Shared NIC")
        groups = next(item["data"]["items"] for item in evidence["dnsGroups"]
                      if item["path"].split("?")[0] == pe_id + "/privateDnsZoneGroups")
        require(len(groups) == 1, "DNS group drift")
        require(groups[0]["id"] == plan["automaticDnsZoneGroupRemovalIdsInOrder"][index],
                "DNS group ID drift")
        require(len(groups[0]["configs"]) == 1 and
                groups[0]["configs"][0]["id"] == (
                    plan["resourceGroupId"] + "/providers/Microsoft.Network/"
                    "privateDnsZones/privatelink.api.azureml.ms"), "Zone link drift")
        require(all(not config["recordSets"] for config in groups[0]["configs"]),
                "DNS records would be affected")
        require(not any(role["scope"].lower().startswith((pe_id.lower(), nic_id.lower()))
                        for role in roles), "Candidate-scoped IAM assignment")
    require(all(item.lower() in by_id(roles) for item in plan["protectedRoleAssignmentIds"]),
            "Protected assignment missing")
    counts = {
        "primaryResources": len(resources),
        "networkResources": sum(item["type"].lower().startswith("microsoft.network/")
                                for item in resources.values()),
        "dnsZones": len(rows(evidence, "zones")),
        "dnsRecordSets": sum(len(item["records"]["data"]["items"])
                             for item in evidence["dns"]),
        "roleAssignments": len(roles),
    }
    require(counts == plan["baselineCounts"], "Baseline count drift")
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    evidence = json.loads(args.evidence.read_text(encoding="utf-8-sig"))
    plan = json.loads(args.plan.read_text(encoding="utf-8-sig"))
    require(hashlib.sha256(args.evidence.read_bytes()).hexdigest().upper()
            == plan["evidenceSha256"], "Evidence hash mismatch")
    print("PASS (offline consistency only):", validate(evidence, plan))


if __name__ == "__main__":
    main()
