"""Focused offline checks against metadata; negative cases are fabricated drift."""

import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "retained_network", ROOT / "infra" / "scripts" / "validate-retained-network.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
DOCS = ROOT / "docs" / "current-state"
PLAN = json.loads((DOCS / "issue148-retained-network-proposal.json").read_text())
EVIDENCE = json.loads((DOCS / PLAN["evidence"]).read_text())


class RetainedNetworkTests(unittest.TestCase):
    def setUp(self):
        self.evidence = copy.deepcopy(EVIDENCE)
        self.plan = copy.deepcopy(PLAN)

    def check_rejected(self, message):
        with self.assertRaisesRegex(ValueError, message):
            MODULE.validate(self.evidence, self.plan)

    def test_observed_links_support_only_proposed_scope(self):
        self.assertEqual(MODULE.validate(self.evidence, self.plan)["networkResources"], 48)

    def test_approved_or_new_consumer_blocks(self):
        self.evidence["endpoints"]["data"]["items"][0]["connections"][0]["status"] = "Approved"
        self.check_rejected("not disconnected")

    def test_provider_nic_link_is_required_not_name_similarity(self):
        nic = next(item for item in self.evidence["nics"]["data"]["items"]
                   if item["id"] == self.plan["automaticNicRemovalIdsInOrder"][0])
        nic["managedBy"] = "/fabricated/unrelated/privateEndpoint"
        self.check_rejected("ownership")

    def test_new_dns_record_blocks_automatic_effect_assumption(self):
        group = self.evidence["dnsGroups"][0]["data"]["items"][0]
        group["configs"][0]["recordSets"] = [{"name": "fabricated-record"}]
        self.check_rejected("DNS records")

    def test_shared_zone_or_iam_delete_is_rejected(self):
        for name in ("dnsZoneDeleteIds", "roleDeleteIds", "explicitNicDeleteIds"):
            with self.subTest(name=name):
                self.plan = copy.deepcopy(PLAN)
                self.plan[name] = ["/fabricated/not-authorized"]
                self.check_rejected("scope expansion")

    def test_incomplete_inventory_is_not_empty(self):
        self.evidence["resources"]["data"]["nextLink"] = "fabricated-next-page"
        self.check_rejected("Incomplete")

    def test_protected_legacy_grant_cannot_be_swept(self):
        protected = self.plan["protectedRoleAssignmentIds"][0].lower()
        self.evidence["roles"]["data"]["items"] = [
            item for item in self.evidence["roles"]["data"]["items"]
            if item["id"].lower() != protected
        ]
        self.check_rejected("Protected assignment")


if __name__ == "__main__":
    unittest.main()
