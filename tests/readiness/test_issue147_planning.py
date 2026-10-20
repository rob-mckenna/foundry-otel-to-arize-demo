"""Offline checks of the public pricing workbook, not deployment validation."""

import ast
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
        for doc in (
            "fresh-foundation-acceptance.md",
            "issue147-cost-estimate.md",
            "issue147-workflow-gates.md",
            "issue147-private-agent-prerequisites.md",
            "issue147-bounded-execution.md",
        ):
            content = (DOCS / doc).read_text(encoding="utf-8")
            for example in re.findall(r"```python\s*\n(.*?)```", content, re.S):
                ast.parse(example, filename=doc)
            for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", content):
                if "://" not in target and not target.startswith("#"):
                    self.assertTrue((DOCS / target.split("#")[0]).exists(), target)

    def test_bounded_followup_provenance_and_cost_reserve_reconcile(self):
        evidence = json.loads((DOCS / "issue147-bounded-execution.json").read_text(encoding="utf-8"))
        self.assertEqual(Decimal(evidence["conditionalPriced24hSubtotalUSD"]), self.subtotal(1).quantize(Decimal(".000001")))
        self.assertIsNone(evidence["allInclusiveTotalUSD"])
        self.assertFalse(evidence["officialValidationCompleted"])
        cache = ROOT / ".azure-sandbox" / "issue147-bounded"
        if cache.exists():
            for file in evidence["publicProof"]:
                self.assertEqual(hashlib.sha256((cache / file["file"]).read_bytes()).hexdigest(), file["sha256"])
            self.assertEqual(
                hashlib.sha256((cache / "security-plan-metadata.json").read_bytes()).hexdigest(),
                evidence["securityMetadata"]["receiptSha256"],
            )
        doc = (DOCS / "issue147-bounded-execution.md").read_text(encoding="utf-8")
        reserve = Decimal(evidence["conditionalPriced24hSubtotalUSD"]) + Decimal(evidence["conditionalFurther30dayReserveUSD"])
        self.assertIn(f"${reserve:.6f}", doc)

    def test_selected_existing_reference_inventory_and_affected_cost_meters(self):
        manifest = json.loads((DOCS / "issue147-first-allocation-manifest.json").read_text(encoding="utf-8"))
        allocation = manifest["predictedFirstAllocation"]
        paths = allocation["freshResourcePaths"]
        self.assertFalse(any("/Microsoft.KeyVault/vaults/" in path for path in paths))
        self.assertFalse(any("pe-kv-" in path for path in paths))
        endpoints = [path for path in paths if "/privateEndpoints/" in path and "/privateDnsZoneGroups/" not in path]
        self.assertEqual(len(endpoints), allocation["newPrivateEndpointCount"])
        self.assertEqual(len(endpoints), 4)
        self.assertEqual(allocation["expectedPrivateEndpointIpSlots"], 6)
        self.assertEqual(allocation["newExternalSecretCount"], 1)
        self.assertEqual(len(manifest["separateFutureIamLease"][0]["secretNames"]), 4)
        self.assertNotIn("Microsoft.KeyVault/vaults/write", manifest["laterExecutorManagementActions"]["freshGroup"])
        cost = manifest["conditionalCostAndLifetime"]
        quantities = cost["selectedAffectedMeterQuantities"]
        baseline = {row["meter"]: row for row in self.evidence["lineItems"]}
        delta = sum(
            (Decimal(str(quantity)) - Decimal(baseline[meter]["quantity"]))
            * Decimal(str(self.evidence["meters"][meter]["retailPrice"]))
            / Decimal(baseline[meter]["unitsPerRate"])
            for meter, quantity in quantities.items()
        )
        selected = self.subtotal(1).quantize(Decimal(".000001")) + delta
        self.assertEqual(selected, Decimal(cost["selectedRouteConditionalPricedSubtotalUSD"]))
        self.assertIn(f"${selected:.6f} USD", self.cost_doc)
        self.assertEqual(quantities, {"pe_hours": 100, "dns_zones": 0, "defender_kv": 0})
        m = self.evidence["meters"]
        tail = Decimal("235.0028") - 7 * Decimal(str(m["dns_zones"]["retailPrice"]))
        tail -= 721 * Decimal(str(m["pe_hours"]["retailPrice"]))
        tail -= 720 * Decimal(str(m["defender_kv"]["retailPrice"]))
        self.assertEqual(tail, Decimal(cost["conditionalFurther30dayReserveUSD"]))
        self.assertIn(f"${selected + tail:.6f} USD", self.cost_doc)
        for path, digest in manifest["committedSourceBindings"].items():
            # Git clean conversion is LF for these source artifacts; checkout
            # bytes are bound independently and are never silently normalized.
            data = (ROOT / path.replace("\\", "/")).read_bytes()
            self.assertEqual(hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
