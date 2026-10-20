"""Offline compiled topology contracts for #153; no Azure CLI/cloud fallback."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]


def compile_bicep(relative):
    cli = os.environ.get("BICEP_CLI") or shutil.which("bicep")
    if not cli:
        raise RuntimeError("Set BICEP_CLI to an existing standalone compiler")
    result = subprocess.run(
        [cli, "build", str(ROOT / relative), "--stdout"],
        capture_output=True, text=True, timeout=120, check=True,
    )
    return json.loads(result.stdout)


def resources(template):
    items = template["resources"]
    return list(items.values()) if isinstance(items, dict) else items


def writable(template):
    for item in resources(template):
        if not item.get("existing"):
            yield item
            if item["type"] == "Microsoft.Resources/deployments":
                yield from writable(item["properties"]["template"])


class PipelineHealthTopologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rollout = compile_bicep("infra/pipeline-health-rollout.bicep")
        cls.health = compile_bicep("infra/modules/function-health.bicep")
        cls.function = compile_bicep("infra/modules/function-app.bicep")
        cls.main = compile_bicep("infra/main.bicep")
        cls.agent = compile_bicep("infra/modules/app-insights.bicep")

    def test_scoped_rollout_has_only_health_pair_and_secret(self):
        actual = {r["type"] for r in writable(self.rollout)}
        self.assertEqual(actual, {
            "Microsoft.Resources/deployments",
            "Microsoft.OperationalInsights/workspaces",
            "Microsoft.Insights/components",
            "Microsoft.KeyVault/vaults/secrets",
        })
        # No export/diagnostic/DCR/event-hub/storage/IAM or parent Function PUT.
        module, = resources(self.rollout)
        self.assertEqual(module["properties"]["mode"], "Incremental")
        self.assertEqual(set(self.rollout["outputs"]), {
            "healthWorkspaceResourceId", "healthComponentResourceId", "functionHealthSecretUri",
        })

    def test_dedicated_workspace_and_bounded_health_without_feedback_routes(self):
        workspace, = [r for r in writable(self.health)
                      if r["type"] == "Microsoft.OperationalInsights/workspaces"]
        component, = [r for r in writable(self.health)
                      if r["type"] == "Microsoft.Insights/components"]
        self.assertIn("'funclaw'", workspace["name"])
        self.assertIn("'funcappi'", component["name"])
        self.assertEqual(component["properties"]["WorkspaceResourceId"],
                         "[resourceId('Microsoft.OperationalInsights/workspaces', "
                         "__bicep.buildResourceName(parameters('projectToken'), parameters('environment'), "
                         "'funclaw', parameters('regionToken')))]")
        self.assertEqual(workspace["properties"]["sku"]["name"], "[parameters('workspaceSkuName')]")
        self.assertEqual(self.health["parameters"]["workspaceSkuName"]["allowedValues"], ["PerGB2018"])
        for name, default, lower, upper in (
            ("retentionInDays", 30, 30, 90), ("dailyQuotaGb", 1, 1, 10),
        ):
            self.assertEqual(self.health["parameters"][name]["defaultValue"], default)
            self.assertEqual(self.health["parameters"][name]["minValue"], lower)
            self.assertEqual(self.health["parameters"][name]["maxValue"], upper)
        for resource in (workspace, component):
            self.assertEqual(resource["tags"], "[variables('requiredTags')]")
            self.assertEqual(resource["properties"]["publicNetworkAccessForIngestion"], "Enabled")
            self.assertEqual(resource["properties"]["publicNetworkAccessForQuery"], "Enabled")
        self.assertIn("'synthetic'", self.health["variables"]["requiredTags"])
        agent_workspace, = [r for r in writable(self.agent)
                            if r["type"] == "Microsoft.OperationalInsights/workspaces"]
        self.assertNotEqual(workspace["name"], agent_workspace["name"])
        agent_export, = [r for r in writable(self.agent)
                         if r["type"] == "Microsoft.OperationalInsights/workspaces/dataExports"]
        self.assertTrue(agent_export["properties"]["enable"])
        self.assertEqual(agent_export["properties"]["tableNames"],
                         ["AppDependencies", "AppRequests", "AppGenAIContent"])

    def test_function_host_worker_reference_and_exact_guard_identities(self):
        function, = [r for r in resources(self.function) if r["type"] == "Microsoft.Web/sites"]
        settings = function["properties"]["siteConfig"]["appSettings"]
        base = {v["name"]: v["value"] for v in self.function["variables"]["baseAppSettings"]}
        self.assertIn("parameters('functionHealthConnectionStringSecretName')",
                      base["APPLICATIONINSIGHTS_CONNECTION_STRING"])
        self.assertNotIn("appInsightsConnectionStringSecretName", base["APPLICATIONINSIGHTS_CONNECTION_STRING"])
        self.assertNotIn("APPINSIGHTS_INSTRUMENTATIONKEY", base)
        self.assertIn(
            "'PIPELINE_EXCLUDED_SERVICE_NAMES', 'value', string(createArray(variables('functionAppName')))",
            settings,
        )
        self.assertIn(
            "'PIPELINE_EXCLUDED_COMPONENT_RESOURCE_IDS', 'value', "
            "string(createArray(reference('functionHealth').outputs.healthComponentResourceId.value))",
            settings,
        )
        self.assertNotIn("DURABLE_ALLOWED_COMPONENT_RESOURCE_ID", base)
        for gate in ("TelemetryTransform", "DurableGenAIOutbox"):
            self.assertEqual(base[f"AzureWebJobs.{gate}.Disabled"], "true")
        extra_type = self.function["parameters"]["extraKeyVaultReferenceAppSettings"]["items"]
        self.assertEqual(set(extra_type["properties"]["settingName"]["allowedValues"]),
                         {"ARIZE_OTLP_ENDPOINT", "ARIZE_SPACE_ID", "ARIZE_API_KEY"})
        module, = [r for r in resources(self.function) if r["name"] == "function-health"]
        self.assertEqual(module["properties"]["parameters"]["keyVaultName"]["value"],
                         "[parameters('keyVaultName')]")

    def test_secret_is_arm_custodied_not_output_or_plaintext_parameter(self):
        secret, = [r for r in writable(self.health)
                   if r["type"] == "Microsoft.KeyVault/vaults/secrets"]
        self.assertIn("ConnectionString", secret["properties"]["value"])
        self.assertIn("reference(", secret["properties"]["value"])
        self.assertEqual(secret["name"],
                         "[format('{0}/{1}', parameters('keyVaultName'), "
                         "parameters('functionHealthConnectionStringSecretName'))]")
        for output in self.health["outputs"].values():
            self.assertNotIn("ConnectionString", output["value"])
        self.assertIn(".secretUriWithVersion",
                      self.health["outputs"]["functionHealthSecretUri"]["value"])
        self.assertNotIn("connectionString", self.health["parameters"])

    def test_secret_has_required_synthetic_tags_and_bounded_expiration(self):
        secret, = [r for r in writable(self.health)
                   if r["type"] == "Microsoft.KeyVault/vaults/secrets"]
        self.assertEqual(secret["tags"], "[variables('requiredTags')]")
        self.assertIn("'synthetic'", self.health["variables"]["requiredTags"])
        self.assertEqual(secret["properties"]["attributes"], {
            "enabled": True,
            "exp": "[parameters('functionHealthSecretExpirationEpoch')]",
        })
        for template in (self.health, self.function, self.rollout, self.main):
            expiry = template["parameters"]["functionHealthSecretExpirationEpoch"]
            self.assertEqual(expiry["type"], "int")
            self.assertEqual(expiry["minValue"], 1)  # Reject zero and negative epochs.
            self.assertEqual(expiry["maxValue"], 2147483647)
            self.assertEqual(expiry["defaultValue"],
                             "[dateTimeToEpoch(dateTimeAdd(utcNow(), 'P90D'))]")

    def test_expiration_override_reaches_health_secret_through_each_caller(self):
        for template, module_name in (
            (self.rollout, "pipeline-function-health"),
            (self.function, "function-health"),
            (self.main, "function-app-deployment"),
        ):
            module, = [r for r in resources(template) if r["name"] == module_name]
            self.assertEqual(
                module["properties"]["parameters"]["functionHealthSecretExpirationEpoch"]["value"],
                "[parameters('functionHealthSecretExpirationEpoch')]",
            )


if __name__ == "__main__":
    unittest.main()
