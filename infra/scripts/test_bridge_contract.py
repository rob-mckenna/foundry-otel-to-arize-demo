import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest


SPEC = importlib.util.spec_from_file_location(
    "bridge", Path(__file__).with_name("prepare-bridge.py"))
bridge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bridge)


class AttachmentInputTests(unittest.TestCase):
    def setUp(self):
        self.document = json.loads((bridge.ROOT / "infra/main.parameters.json").read_text())
        self.p = self.document["parameters"]

    def test_synthetic_example_and_bound_owner_evidence(self):
        values = bridge.validate(self.document)
        evidence = {
            "parametersSha256": hashlib.sha256(json.dumps(
                values, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "confirmations": dict.fromkeys(bridge.REQUIRED_EVIDENCE, True),
        }
        bridge.validate_attestation(evidence, values)
        changed = dict(values, eventHubName="different-hub")
        with self.assertRaisesRegex(ValueError, "exact parameter"):
            bridge.validate_attestation(evidence, changed)
        evidence["confirmations"]["privateKeyVaultReferencesResolved"] = False
        with self.assertRaisesRegex(ValueError, "incomplete"):
            bridge.validate_attestation(evidence, values)

    def test_health_sink_must_not_share_either_agent_identity(self):
        for key, value in (
            ("functionHealthComponentResourceId", self.p["agentComponentResourceId"]["value"]),
            ("functionHealthWorkspaceResourceId",
             self.p["functionHealthWorkspaceResourceId"]["value"].replace(
                 "synthetic-health-law", self.p["workspaceName"]["value"])),
        ):
            with self.subTest(key=key):
                document = copy.deepcopy(self.document)
                document["parameters"][key]["value"] = value
                with self.assertRaisesRegex(ValueError, "separate"):
                    bridge.validate(document)

    def test_unversioned_target_and_destructive_partial_contract_rejected(self):
        self.p["existingAgent"]["value"]["agentVersion"] = "latest"
        with self.assertRaisesRegex(ValueError, "numbered"):
            bridge.validate(self.document)
        del self.p["existingExportEnabled"]
        with self.assertRaisesRegex(ValueError, "parameter names"):
            bridge.validate(self.document)

    def test_no_auth_storage_or_package_fallback(self):
        cases = (
            ("DURABLE_GENAI_ENABLED", "false", "legacy"),
            ("AzureWebJobsStorage", "synthetic-disallowed", "legacy"),
            ("ARIZE_API_KEY", "synthetic-disallowed", "Key Vault"),
            ("AzureWebJobsStorage__blobServiceUri", "https://other.blob.core.windows.net",
             "URI must match"),
            ("WEBSITE_RUN_FROM_PACKAGE", "https://public.invalid/package.zip?sig=synthetic",
             "immutable"),
            ("AZURE_CLIENT_ID", "synthetic-client", "system-assigned"),
            ("PIPELINE_EXCLUDED_SERVICE_NAMES", "{}", "JSON string array"),
        )
        for key, value, message in cases:
            with self.subTest(key=key):
                document = copy.deepcopy(self.document)
                document["parameters"]["existingFunctionAppSettings"]["value"][key] = value
                with self.assertRaisesRegex(ValueError, message):
                    bridge.validate(document)

    def test_input_paths_cannot_escape_or_read_secret_configuration(self):
        with self.assertRaisesRegex(ValueError, "inside this worktree"):
            bridge.local_json(bridge.ROOT.parent / "not-read.json")
        with self.assertRaisesRegex(ValueError, "secret configuration"):
            bridge.local_json(bridge.ROOT / ".env")


class CompiledAttachmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        local = bridge.ROOT / ".tools/bicep.exe"
        compiler = os.environ.get("BICEP_CLI") or shutil.which("bicep")
        if not compiler and local.is_file():
            compiler = str(local)
        if not compiler:
            raise unittest.SkipTest("standalone Bicep compiler missing; compiled contract NOT validated")
        result = subprocess.run(
            [compiler, "build", str(bridge.ROOT / "infra/main.bicep"), "--stdout"],
            capture_output=True, text=True, check=True, timeout=120,
        )
        cls.template = json.loads(result.stdout)
        resources = cls.template["resources"]
        cls.resources = list(resources.values()) if isinstance(resources, dict) else resources
        cls.by_type = {r["type"]: r for r in cls.resources if not r.get("existing")}

    def test_only_bounded_child_and_state_writes_not_base_resources(self):
        self.assertEqual(set(self.by_type), {
            "Microsoft.Web/sites/config",
            "Microsoft.OperationalInsights/workspaces/dataExports",
            "Microsoft.Resources/deployments",
        })
        nested = self.by_type["Microsoft.Resources/deployments"]["properties"]["template"]
        self.assertEqual({r["type"] for r in nested["resources"]}, {
            "Microsoft.Storage/storageAccounts/blobServices/containers",
            "Microsoft.Authorization/roleDefinitions", "Microsoft.Authorization/roleAssignments",
        })
        assignment = next(r for r in nested["resources"] if r["type"].endswith("/roleAssignments"))
        self.assertIn("genai-correlation", assignment["scope"])
        self.assertIn("parameters('functionPrincipalId')", assignment["properties"]["principalId"])
        definition = next(r for r in nested["resources"] if r["type"].endswith("/roleDefinitions"))
        permissions = definition["properties"]["permissions"][0]
        self.assertEqual(permissions["actions"], [])
        self.assertEqual(set(permissions["dataActions"]), {
            "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/tags/write",
            "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/filter/action",
        })
        container = next(r for r in nested["resources"] if r["type"].endswith("/containers"))
        self.assertEqual(container["properties"]["publicAccess"], "None")

    def test_settings_and_export_preserve_reviewed_baselines(self):
        config = self.by_type["Microsoft.Web/sites/config"]
        self.assertEqual(config["properties"],
                         "[union(parameters('existingFunctionAppSettings'), variables('runtimeSettings'))]")
        export = self.by_type["Microsoft.OperationalInsights/workspaces/dataExports"]["properties"]
        self.assertEqual(export["enable"], "[parameters('existingExportEnabled')]")
        self.assertIn("union(parameters('existingExportTableNames')", export["tableNames"])
        for table in ("AppRequests", "AppDependencies", "AppGenAIContent"):
            self.assertIn(table, export["tableNames"])
        self.assertIn("parameters('eventHubNamespaceName')", export["destination"]["resourceId"])
        self.assertEqual(export["destination"]["metaData"]["eventHubName"], "[parameters('eventHubName')]")

    def test_runtime_preparation_is_disabled_with_health_source_policy(self):
        settings = self.template["variables"]["runtimeSettings"]
        for function in ("TelemetryTransform", "DurableGenAIOutbox"):
            self.assertEqual(settings[f"AzureWebJobs.{function}.Disabled"], "true")
        self.assertNotIn("DURABLE_GENAI_ENABLED", settings)
        self.assertIn("functionHealthConnectionStringSecretName",
                      settings["APPLICATIONINSIGHTS_CONNECTION_STRING"])
        self.assertIn("functionHealthComponentResourceId",
                      settings["PIPELINE_EXCLUDED_COMPONENT_RESOURCE_IDS"])
        self.assertIn("union(", settings["PIPELINE_EXCLUDED_SERVICE_NAMES"])
        self.assertEqual(settings["DURABLE_ALLOWED_COMPONENT_RESOURCE_ID"],
                         "[parameters('agentComponentResourceId')]")
        self.assertEqual(set(self.template["parameters"]), bridge.PARAMETERS)


if __name__ == "__main__":
    unittest.main()
