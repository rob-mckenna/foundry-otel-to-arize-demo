"""Offline checks of the public pricing workbook, not deployment validation."""

import hashlib
import json
from decimal import Decimal
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs" / "current-state"


class PlanningEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(
            (DOCS / "issue147-planning-evidence.json").read_text(encoding="utf-8")
        )
        cls.cost_doc = (DOCS / "issue147-cost-estimate.md").read_text(encoding="utf-8")

    def subtotal(self, instances):
        total = Decimal(0)
        for row in self.evidence["lineItems"]:
            meter = self.evidence["meters"][row["meter"]]
            quantity = Decimal(row["quantity"])
            rate = Decimal(str(meter["retailPrice"]))
            divisor = Decimal(row["unitsPerRate"])
            self.assertGreater(divisor, 0)
            total += quantity * rate / divisor * (
                instances if row["scalesWithAllocatedInstances"] else 1
            )
        return total

    def test_displayed_totals_and_scale_sensitivity_recompute(self):
        for scenario in self.evidence["scenarios"]:
            with self.subTest(instances=scenario["allocatedInstances"]):
                actual = self.subtotal(scenario["allocatedInstances"])
                stated = Decimal(scenario["conditionalPricedSubtotalUSD"])
                self.assertLess(abs(actual - stated), Decimal("0.000000001"))
                self.assertIn(f"${actual:.6f} USD", self.cost_doc)
        meters = self.evidence["meters"]
        hourly = (
            Decimal(str(meters["ep1_core"]["retailPrice"]))
            + Decimal("3.5") * Decimal(str(meters["ep1_memory"]["retailPrice"]))
            + Decimal(str(meters["defender_app"]["retailPrice"]))
        )
        connection_delta = 19 * 2 * Decimal(str(meters["eh_connections"]["retailPrice"]))
        self.assertEqual(self.subtotal(20) - self.subtotal(1), 19 * 24 * hourly + connection_delta)

    def test_retained_tail_uses_hours_and_capacity_month_not_first_day(self):
        m = self.evidence["meters"]
        rate = lambda key: Decimal(str(m[key]["retailPrice"]))
        fixed = 720 * (
            rate("ep1_core") + Decimal("3.5") * rate("ep1_memory")
            + 5 * rate("pe_hours") + rate("eh_tu")
        )
        capacity = 10 * rate("blob_capacity") + rate("queue_capacity") + rate("table_capacity")
        zones = 7 * rate("dns_zones")
        base_tail = fixed + capacity + zones
        security_tail = 720 * sum(
            rate(key) for key in ("defender_storage", "defender_kv", "defender_app", "defender_arm")
        )
        self.assertIn(f"${base_tail:.3f}", self.cost_doc)
        self.assertIn(f"${base_tail + security_tail:.4f}", self.cost_doc)
        rounding = 5 * rate("pe_hours") + rate("eh_tu")
        connections = 3 * 4 * rate("eh_connections")
        self.assertIn(f"${base_tail + security_tail + rounding + connections:.4f}", self.cost_doc)
        self.assertGreater(base_tail, self.subtotal(1))

    def test_public_prices_are_complete_unique_unit_matched_and_not_free_tiers(self):
        evidence = self.evidence
        self.assertEqual(
            set(evidence["meters"]),
            {row["meter"] for row in evidence["lineItems"]},
        )
        identities = []
        for key, meter in evidence["meters"].items():
            with self.subTest(meter=key):
                response = evidence["responses"][meter["response"]]
                self.assertTrue(response["complete"])
                self.assertTrue(response["source"].startswith("https://prices.azure.com/api/retail/prices?"))
                self.assertGreaterEqual(response["pageCount"], 1)
                self.assertRegex(response["sha256"], r"^[a-f0-9]{64}$")
                self.assertGreater(Decimal(str(meter["retailPrice"])), 0)
                self.assertEqual(meter["currencyCode"], evidence["currency"])
                self.assertEqual(meter["type"], "Consumption")
                identities.append((meter["meterId"], meter["meterName"], meter["skuName"]))
        self.assertEqual(len(identities), len(set(identities)))
        for row in evidence["lineItems"]:
            meter = evidence["meters"][row["meter"]]
            if meter["unitOfMeasure"] == "10K":
                self.assertEqual(Decimal(row["unitsPerRate"]), 10000)
            if meter["unitOfMeasure"] == "1M":
                self.assertEqual(Decimal(row["unitsPerRate"]), 1000000)
            if meter["unitOfMeasure"] == "1 GB/Month":
                self.assertEqual(Decimal(row["unitsPerRate"]), evidence["capacityMonthDays"])

    def test_workflow_provenance_and_no_fabricated_total(self):
        evidence = self.evidence
        self.assertIsNone(evidence["allInclusiveTotal"])
        self.assertTrue(evidence["unresolvedAddends"])
        for scenario in evidence["scenarios"]:
            self.assertFalse(scenario["effectiveMaximumVerified"])
            self.assertFalse(scenario["volumeEnvelopeEnforced"])
        workflow = evidence["workflow"]
        self.assertFalse(workflow["externalProfileRead"])
        self.assertRegex(workflow["commit"], r"^[a-f0-9]{40}$")
        paths = set()
        for file in workflow["files"]:
            self.assertNotIn(file["path"], paths)
            paths.add(file["path"])
            self.assertRegex(file["sha256"], r"^[a-f0-9]{64}$")
            self.assertIn("/" + workflow["commit"] + "/", file["source"])
        # If the optional ignored public cache exists, validate bytes, not just URLs.
        team_root = ROOT.parents[1] if ROOT.parent.name == ".worktrees" else ROOT
        cache = team_root / ".azure-sandbox" / "issue147-workflow" / "qa-followup-20261019"
        if cache.exists():
            for file in workflow["files"]:
                data = (cache / Path(file["path"])).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), file["sha256"])
            for name, response in evidence["responses"].items():
                data = (cache / f"price-{name}.json").read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), response["sha256"])
        for doc in ("fresh-foundation-acceptance.md", "issue147-cost-estimate.md", "issue147-workflow-gates.md"):
            for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", (DOCS / doc).read_text(encoding="utf-8")):
                if "://" not in target and not target.startswith("#"):
                    self.assertTrue((DOCS / target.split("#")[0]).exists(), target)


if __name__ == "__main__":
    unittest.main()
