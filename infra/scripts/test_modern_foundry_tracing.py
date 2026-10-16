import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "tracing", ROOT / "infra" / "scripts" / "validate-modern-foundry-tracing.py"
)
tracing = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tracing)
PROJECT = (
    "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/test-rg/"
    "providers/Microsoft.CognitiveServices/accounts/test-account/projects/test-project"
)
TARGET = (
    "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/test-rg/"
    "providers/Microsoft.Insights/components/test-appi"
)
NAME = "manual-link"


class AssociationTests(unittest.TestCase):
    def setUp(self):
        self.document = {
            "connections": [{
                "id": f"{PROJECT}/connections/{NAME}", "name": NAME,
                "category": "AppInsights", "target": TARGET, "resourceId": TARGET,
                "authType": "ApiKey",
            }],
            "hasNext": None,
        }

    def check(self, document=None, auth="ApiKey"):
        return tracing.validate_association(
            self.document if document is None else document, PROJECT, NAME, TARGET, auth
        )

    def test_manual_link_is_not_migration_or_trace_proof(self):
        receipt = self.check()
        self.assertTrue(receipt["associationVerified"])
        self.assertFalse(receipt["traceDeliveryVerified"])
        self.assertEqual(receipt["connectionResourceId"], f"{PROJECT}/connections/{NAME}")
        with self.assertRaisesRegex(ValueError, "authType"):
            self.check(auth="ProjectManagedIdentity")
        self.document["connections"][0]["authType"] = "ProjectManagedIdentity"
        self.assertEqual(self.check(auth="ProjectManagedIdentity")["authType"], "ProjectManagedIdentity")

    def test_missing_duplicate_paginated_and_mismatched_associations_fail(self):
        for field in ["id", "name", "category", "target", "resourceId", "authType"]:
            with self.subTest(field=field):
                document = copy.deepcopy(self.document)
                document["connections"][0][field] = "unrelated"
                with self.assertRaisesRegex(ValueError, field):
                    self.check(document)
        for connections in [[], self.document["connections"] * 2]:
            with self.assertRaisesRegex(ValueError, "exactly one"):
                self.check({"connections": connections})
        with self.assertRaisesRegex(ValueError, "pagination"):
            self.check({**self.document, "hasNext": "https://not-followed.invalid"})
        for document in [[], {"connections": [None]}, {"connections": None}]:
            with self.assertRaisesRegex(ValueError, "object|exactly one"):
                self.check(document)

    def test_arm_case_variation_is_allowed_but_target_suffix_is_not(self):
        self.document["connections"][0]["target"] = TARGET.upper()
        self.assertTrue(self.check()["associationVerified"])
        self.document["connections"][0]["target"] = TARGET + "-other"
        with self.assertRaisesRegex(ValueError, "target"):
            self.check()

    def test_apikey_and_sharing_cannot_satisfy_migration_or_changed_sharing(self):
        self.document["connections"][0]["isSharedToAll"] = True
        receipt = tracing.validate_association(self.document, PROJECT, NAME, TARGET, "ApiKey", "projectShared")
        self.assertTrue(receipt["sharingVerified"])
        with self.assertRaisesRegex(ValueError, "authType"):
            tracing.validate_association(self.document, PROJECT, NAME, TARGET, "ProjectManagedIdentity", "projectShared")
        for actual in [True, None, 0, "false"]:
            self.document["connections"][0]["isSharedToAll"] = actual
            with self.assertRaisesRegex(ValueError, "isSharedToAll"):
                tracing.validate_association(self.document, PROJECT, NAME, TARGET, "ApiKey", "private")
        self.document["connections"][0]["isSharedToAll"] = False
        self.assertTrue(tracing.validate_association(
            self.document, PROJECT, NAME, TARGET, "ApiKey", "private"
        )["sharingVerified"])

    @patch.object(tracing, "read_association")
    def test_cli_forwards_explicit_apikey_and_sharing_without_migration(self, read):
        read.return_value = {"associationVerified": True, "traceDeliveryVerified": False}
        arguments = [
            "validate-modern-foundry-tracing.py", "--project-resource-id", PROJECT,
            "--connection-name", NAME, "--app-insights-resource-id", TARGET,
            "--expected-auth-type", "ApiKey", "--expected-sharing", "private",
        ]
        with patch("sys.argv", arguments), patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(tracing.main(), 0)
        read.assert_called_once_with(PROJECT, NAME, TARGET, "ApiKey", "private")
        self.assertFalse(json.loads(output.getvalue())["traceDeliveryVerified"])
        read.side_effect = ValueError("Expected exactly one AppInsights connection.")
        with patch("sys.argv", arguments), patch("sys.stderr", new_callable=io.StringIO):
            self.assertEqual(tracing.main(), 1)

    @patch.object(tracing.shutil, "which", return_value="az.cmd")
    @patch.object(tracing.subprocess, "run")
    def test_live_caller_uses_only_projected_get_and_verifies_result(self, run, _which):
        run.return_value = subprocess.CompletedProcess([], 0, json.dumps(self.document), "")
        receipt = tracing.read_association(PROJECT, NAME, TARGET, "ApiKey")
        self.assertTrue(receipt["associationVerified"])
        command = run.call_args.args[0]
        self.assertEqual(command[command.index("--method") + 1], "get")
        self.assertEqual(command[command.index("--subscription") + 1], PROJECT.split("/")[2])
        self.assertEqual(command[command.index("--query") + 1], tracing.PROJECTION)
        self.assertNotIn("credentials", tracing.PROJECTION)
        self.assertNotIn("ApplicationInsightsConnectionString", tracing.PROJECTION)
        self.assertEqual(run.call_args.kwargs["timeout"], 90)
        run.return_value.stdout = json.dumps({"connections": []})
        with self.assertRaisesRegex(ValueError, "exactly one"):
            tracing.read_association(PROJECT, NAME, TARGET, "ApiKey")

    @patch.object(tracing.shutil, "which", return_value="az.cmd")
    @patch.object(tracing.subprocess, "run")
    def test_failed_timeout_and_invalid_readback_never_emit_raw_response(self, run, _which):
        run.return_value = subprocess.CompletedProcess([], 1, "private-response", "private-error")
        with self.assertRaisesRegex(ValueError, "Raw CLI errors suppressed") as error:
            tracing.read_association(PROJECT, NAME, TARGET, "ApiKey")
        self.assertNotIn("private-", str(error.exception))
        run.return_value = subprocess.CompletedProcess([], 0, "private-invalid-json", "")
        with self.assertRaisesRegex(ValueError, "invalid JSON") as error:
            tracing.read_association(PROJECT, NAME, TARGET, "ApiKey")
        self.assertNotIn("private-", str(error.exception))
        run.side_effect = subprocess.TimeoutExpired("az", 90)
        with self.assertRaisesRegex(ValueError, "90 seconds"):
            tracing.read_association(PROJECT, NAME, TARGET, "ApiKey")

    @patch.object(tracing.subprocess, "run")
    def test_invalid_target_or_nonproject_scope_is_rejected_before_cli(self, run):
        for project, name, target in [
            (PROJECT + "/connections/x", NAME, TARGET),
            (PROJECT, NAME, TARGET + "/x"),
            (PROJECT.replace("00000000", "--------"), NAME, TARGET),
            (PROJECT + "?api-version=unreviewed", NAME, TARGET),
            (PROJECT, NAME, TARGET + "?unreviewed=true"),
            (PROJECT, "../other", TARGET),
        ]:
            with self.subTest(project=project, name=name, target=target):
                with self.assertRaises(ValueError):
                    tracing.read_association(project, name, target, "ApiKey")
        run.assert_not_called()


def resources(template):
    collection = template["resources"]
    return list(collection.values()) if isinstance(collection, dict) else collection


def assert_connection_contract(test, template):
    test.assertEqual(template["parameters"]["appInsightsConnectionString"]["type"].lower(), "securestring")
    test.assertEqual(template["parameters"]["tracingAssociationMode"]["defaultValue"], "preserveExisting")
    test.assertFalse(template["parameters"]["appInsightsConnectionPropertiesReviewed"]["defaultValue"])
    test.assertEqual(
        template["parameters"]["tracingAssociationMode"]["allowedValues"],
        ["preserveExisting", "ApiKey", "ProjectManagedIdentity"],
    )
    test.assertEqual(len(resources(template)), 1, "Entrypoint must not deploy parents, roles or networks.")
    module = resources(template)[0]
    test.assertEqual(module["type"], "Microsoft.Resources/deployments")
    test.assertEqual(module["name"], "modern-foundry-app-insights")
    test.assertEqual(module["properties"]["mode"], "Incremental")
    test.assertEqual(
        module["condition"],
        "[or(equals(parameters('tracingAssociationMode'), 'ApiKey'), equals(parameters('tracingAssociationMode'), 'ProjectManagedIdentity'))]",
    )
    test.assertEqual(
        module["properties"]["parameters"]["connectionAuthType"],
        "[if(equals(parameters('tracingAssociationMode'), 'ApiKey'), createObject('value', 'ApiKey'), createObject('value', 'ProjectManagedIdentity'))]",
    )
    test.assertEqual(
        module["properties"]["parameters"]["reviewedProperties"],
        "[if(parameters('appInsightsConnectionPropertiesReviewed'), createObject('value', 1), createObject('value', 0))]",
    )
    test.assertEqual(
        module["properties"]["parameters"]["appInsightsConnectionString"]["value"],
        "[parameters('appInsightsConnectionString')]",
    )
    child = module["properties"]["template"]
    test.assertEqual(child["parameters"]["appInsightsConnectionString"]["type"].lower(), "securestring")
    test.assertEqual(child["parameters"]["appInsightsConnectionString"]["minLength"], 1)
    test.assertEqual(child["parameters"]["reviewedProperties"]["minValue"], 1)
    test.assertEqual(child["parameters"]["connectionAuthType"]["allowedValues"], ["ApiKey", "ProjectManagedIdentity"])
    test.assertEqual(len(resources(child)), 1, "Association module must not deploy parents, roles or networks.")
    connection = resources(child)[0]
    test.assertEqual(connection["type"], "Microsoft.CognitiveServices/accounts/projects/connections")
    test.assertEqual(connection["apiVersion"], "2025-09-01")
    test.assertEqual(
        connection["name"],
        "[format('{0}/{1}/{2}', parameters('accountName'), parameters('projectName'), parameters('connectionName'))]",
    )
    test.assertEqual(
        connection["properties"],
        "[if(equals(parameters('connectionAuthType'), 'ApiKey'), variables('apiKeyProperties'), variables('managedIdentityProperties'))]",
    )
    api_key = child["variables"]["apiKeyProperties"]
    managed_identity = child["variables"]["managedIdentityProperties"]
    for properties, auth_type in [(api_key, "ApiKey"), (managed_identity, "ProjectManagedIdentity")]:
        test.assertEqual(properties["category"], "AppInsights")
        test.assertEqual(properties["authType"], auth_type)
        test.assertEqual(properties["target"], "[parameters('appInsightsResourceId')]")
        test.assertEqual(properties["metadata"]["ResourceId"], "[parameters('appInsightsResourceId')]")
        test.assertEqual(properties["isSharedToAll"], "[equals(parameters('connectionSharing'), 'projectShared')]")
    test.assertEqual(api_key["credentials"], {"key": "[parameters('appInsightsConnectionString')]"})
    test.assertFalse(api_key["useWorkspaceManagedIdentity"])
    test.assertNotIn("ApplicationInsightsConnectionString", api_key["metadata"])
    test.assertNotIn("credentials", managed_identity)
    test.assertEqual(
        managed_identity["metadata"]["ApplicationInsightsConnectionString"],
        "[parameters('appInsightsConnectionString')]",
    )
    for output in [*template.get("outputs", {}).values(), *child.get("outputs", {}).values()]:
        test.assertNotIn("ConnectionString", json.dumps(output))


class CompiledContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Compile current sources in memory, never trust preserved or stale build receipts.
        bicep = os.environ.get("BICEP_CLI") or shutil.which("bicep")
        source = str(ROOT / "infra" / "modern-foundry-tracing.bicep")
        if bicep:
            command = [bicep, "build", source]
        else:
            az = shutil.which("az")
            if not az:
                raise RuntimeError("Install Bicep or Azure CLI; compiled contracts are required.")
            command = [az, "bicep", "build", "--file", source]
        result = subprocess.run(
            [*command, "--stdout"],
            capture_output=True, text=True, timeout=120, check=False,
        )
        if result.returncode:
            raise RuntimeError(f"Bicep build failed:\n{result.stderr}")
        cls.template = json.loads(result.stdout)

    def test_current_compilation_emits_only_secure_explicitly_gated_connection(self):
        assert_connection_contract(self, self.template)

    def test_real_compiled_contract_mutations_are_rejected(self):
        for mutation in [
            "authType", "target", "secureParameter", "childSecureParameter", "output",
            "apiKeyCredential", "activeGate", "reviewGate", "sharing", "parentWrite",
            "childParentWrite", "connectionName", "metadataRoutingLeak", "mode",
        ]:
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(self.template)
                module = resources(changed)[0]
                child = module["properties"]["template"]
                properties = child["variables"]["apiKeyProperties"]
                if mutation in {"authType", "target"}:
                    properties[mutation] = "unsafe-mutation"
                elif mutation == "secureParameter":
                    changed["parameters"]["appInsightsConnectionString"]["type"] = "string"
                elif mutation == "childSecureParameter":
                    child["parameters"]["appInsightsConnectionString"]["type"] = "string"
                elif mutation == "output":
                    changed["outputs"]["leak"] = {"type": "string", "value": "[parameters('appInsightsConnectionString')]"}
                elif mutation == "apiKeyCredential":
                    properties["credentials"]["key"] = ""
                elif mutation == "activeGate":
                    module["condition"] = True
                elif mutation == "reviewGate":
                    child["parameters"]["reviewedProperties"]["minValue"] = 0
                elif mutation == "sharing":
                    properties["isSharedToAll"] = True
                elif mutation in {"parentWrite", "childParentWrite"}:
                    # Compilers can use object or array resource collections.
                    collection = (changed if mutation == "parentWrite" else child)["resources"]
                    if isinstance(collection, dict):
                        collection["extra"] = {}
                    else:
                        collection.append({})
                elif mutation == "connectionName":
                    resources(child)[0]["name"] = "generated-duplicate-name"
                elif mutation == "metadataRoutingLeak":
                    properties["metadata"]["ApplicationInsightsConnectionString"] = "[parameters('appInsightsConnectionString')]"
                else:
                    module["properties"]["mode"] = "Complete"
                with self.assertRaises(AssertionError):
                    assert_connection_contract(self, changed)

    def test_profiles_preserve_and_secure_example_uses_only_pinned_vault_reference(self):
        for filename in [
            "modern-foundry-tracing.parameters.json",
            "modern-foundry-tracing.dev.parameters.json",
        ]:
            with self.subTest(filename=filename):
                parameters = json.loads((ROOT / "infra" / filename).read_text())["parameters"]
                self.assertEqual(parameters["tracingAssociationMode"]["value"], "preserveExisting")
                self.assertFalse(parameters["appInsightsConnectionPropertiesReviewed"]["value"])
                self.assertNotIn("appInsightsConnectionString", parameters)
        example = json.loads(
            (ROOT / "infra" / "modern-foundry-tracing.secure-reference.parameters.json").read_text()
        )["parameters"]
        self.assertEqual(example["tracingAssociationMode"]["value"], "preserveExisting")
        self.assertFalse(example["appInsightsConnectionPropertiesReviewed"]["value"])
        secret = example["appInsightsConnectionString"]
        self.assertNotIn("value", secret)
        self.assertTrue(secret["reference"]["secretVersion"])
        self.assertIn("/providers/Microsoft.KeyVault/vaults/", secret["reference"]["keyVault"]["id"])


if __name__ == "__main__":
    unittest.main()
