"""Fresh-source, compiled ARM contracts. Never contacts Azure or skips compilation."""
from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("foundation", Path(__file__).with_name("validate-modern-foundation.py"))
foundation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(foundation)


def compile_bicep(path):
    executable = os.environ.get("BICEP_CLI") or shutil.which("bicep")
    if not executable:
        raise RuntimeError("Standalone BICEP_CLI required; no auto-install/cloud fallback")
    result = subprocess.run([executable, "build", str(ROOT / path), "--stdout"],
                            text=True, capture_output=True, timeout=120, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return json.loads(result.stdout)


def resources(template, kind=None, writable=True):
    collection = template["resources"]
    collection = collection.values() if isinstance(collection, dict) else collection
    return [r for r in collection if (not writable or not r.get("existing", False))
            and (kind is None or r["type"] == kind)]


def module(template, name):
    return next(r for r in resources(template, "Microsoft.Resources/deployments") if r["name"] == name)


def child(template, name):
    return module(template, name)["properties"]["template"]


def all_templates(template):
    yield template
    for resource in resources(template, "Microsoft.Resources/deployments"):
        yield from all_templates(resource["properties"]["template"])


def evaluate_vault_expression(expression, parameters, references):
    """Evaluate the compiled ARM subset used by vault selection, with lazy if."""
    def evaluate(text):
        text = text.strip()
        if text.startswith("'") and text.endswith("'"):
            return text[1:-1]
        match = re.match(r"(\w+)\(", text)
        if not match:
            raise AssertionError(f"Unsupported ARM expression: {text}")
        depth, quoted, start, args = 1, False, match.end(), []
        for index in range(start, len(text)):
            char = text[index]
            if char == "'":
                quoted = not quoted
            if quoted:
                continue
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    if text[start:index].strip():
                        args.append(text[start:index])
                    break
            elif char == "," and depth == 1:
                args.append(text[start:index])
                start = index + 1
        name = match[1]
        if name == "if":
            value = evaluate(args[1] if evaluate(args[0]) else args[2])
        elif name == "reference":
            value = references[evaluate(args[0])]
        elif name == "parameters":
            value = parameters[evaluate(args[0])]
        else:
            values = [evaluate(arg) for arg in args]
            operations = {
                "equals": lambda a, b: a == b,
                "null": lambda: None,
                "createArray": lambda *items: list(items),
                "createObject": lambda *items: dict(zip(items[::2], items[1::2])),
                "concat": lambda *items: sum(items, []),
                "resourceId": lambda kind, name: f"/subscriptions/synthetic/resourceGroups/synthetic/providers/{kind}/{name}",
                "subscriptionResourceId": lambda kind, name: f"/subscriptions/synthetic/providers/{kind}/{name}",
                "guid": lambda *items: str(uuid.uuid5(uuid.UUID("11fb06fb-712d-4ddd-98c7-e71bbd588830"), "-".join(items))),
                "variables": lambda name: references["variables"][name],
            }
            value = operations[name](*values)
        for property_name in text[index + 1:].split(".")[1:]:
            value = value[property_name]
        return value
    return evaluate(expression.removeprefix("[").removesuffix("]"))


class CompiledModernFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = compile_bicep("infra/main.bicep")
        cls.function = child(cls.main, "function-app-deployment")
        cls.network = child(cls.main, "private-network")

    def test_modern_only_resource_inventory_and_version_pins(self):
        types = {r["type"] for t in all_templates(self.main) for r in resources(t)}
        self.assertNotIn("Microsoft.MachineLearningServices/workspaces", types)
        self.assertNotIn("Microsoft.Insights/diagnosticSettings", types)
        self.assertTrue({
            "Microsoft.CognitiveServices/accounts", "Microsoft.CognitiveServices/accounts/projects",
            "Microsoft.CognitiveServices/accounts/deployments",
            "Microsoft.Network/privateEndpoints", "Microsoft.Network/privateEndpoints/privateDnsZoneGroups",
            "Microsoft.Network/privateDnsZones", "Microsoft.Network/privateDnsZones/virtualNetworkLinks",
            "Microsoft.OperationalInsights/workspaces/dataExports",
        }.issubset(types))
        for t in all_templates(self.main):
            for r in resources(t):
                self.assertFalse(any(x in r["type"] for x in ("Search/", "DocumentDB/", "ContainerRegistry/", "virtualMachines")))
                if r["type"].startswith("Microsoft.CognitiveServices/"):
                    self.assertEqual(r["apiVersion"], "2025-09-01")
                if r["type"] == "Microsoft.Resources/deployments":
                    self.assertEqual(r["properties"]["mode"], "Incremental")

    def test_account_project_controls_scoped_published_role_and_outputs(self):
        t = child(self.main, "modern-foundry-foundation")
        account, = resources(t, "Microsoft.CognitiveServices/accounts")
        project, = resources(t, "Microsoft.CognitiveServices/accounts/projects")
        self.assertEqual(account["kind"], "AIServices")
        self.assertEqual(account["sku"], {"name": "S0"})
        self.assertEqual(account["properties"], {
            "allowProjectManagement": True, "customSubDomainName": "[parameters('customSubDomainName')]",
            "disableLocalAuth": True, "publicNetworkAccess": "Disabled",
            "networkAcls": {"defaultAction": "Deny", "bypass": "None"},
        })
        for r in (account, project):
            self.assertEqual(r["identity"], {"type": "SystemAssigned"})
            self.assertEqual(r["tags"], "[variables('requiredTags')]")
            self.assertIn("buildRequiredTags", t["variables"]["requiredTags"])
            self.assertEqual(r["location"], "[parameters('location')]")
        self.assertEqual(set(project["properties"]), {"displayName", "description"})
        role, = resources(t, "Microsoft.Authorization/roleAssignments")
        self.assertEqual(t["variables"]["foundryUserRoleId"], "53ca6127-db72-4b80-b1b0-d745d6d5456d")
        self.assertEqual(role["scope"], "[resourceId('Microsoft.CognitiveServices/accounts', parameters('accountName'))]")
        self.assertEqual(role["properties"]["principalId"],
                         "[reference('project', '2025-09-01', 'full').identity.principalId]")
        self.assertIn("guid(", role["name"])
        self.assertEqual(t["outputs"]["foundryProjectEndpoint"]["value"],
                         "[format('https://{0}.services.ai.azure.com/api/projects/{1}', parameters('customSubDomainName'), parameters('projectName'))]")
        kv = module(self.main, "key-vault-deployment")["properties"]["parameters"]
        self.assertNotIn("readerPrincipalIds", kv)

    def test_explicit_model_without_defaults_upgrade_or_spillover(self):
        t = child(self.main, "modern-foundry-model")
        deployment, = resources(t, "Microsoft.CognitiveServices/accounts/deployments")
        for name in ("accountName", "modelDeploymentName", "modelFormat", "modelName", "modelVersion",
                     "modelDeploymentSkuName", "modelDeploymentCapacity", "modelVersionUpgradeOption"):
            self.assertNotIn("defaultValue", self.main["parameters"][name])
            self.assertNotIn("defaultValue", t["parameters"][name])
        self.assertEqual(deployment["sku"], {
            "name": "[parameters('modelDeploymentSkuName')]",
            "capacity": "[parameters('modelDeploymentCapacity')]",
        })
        self.assertEqual(t["parameters"]["modelDeploymentCapacity"]["minValue"], 1)
        self.assertEqual(self.main["parameters"]["modelDeploymentApproved"]["allowedValues"], [True])
        self.assertNotIn("defaultValue", self.main["parameters"]["modelDataResidencyApproval"])
        # Bicep emits union() to omit raiPolicyName, not null/implicit policy.
        self.assertIn("'modelVersion'", deployment["properties"])
        self.assertIn("'modelVersionUpgradeOption'", deployment["properties"])
        for field in ("scaleSettings", "spilloverDeploymentName", "parentDeploymentName"):
            self.assertNotIn(field, deployment["properties"])

    def test_fresh_vnet_subnets_dns_links_and_existing_no_put_conditions(self):
        vnet, = resources(self.network, "Microsoft.Network/virtualNetworks")
        self.assertEqual(vnet["condition"], "[equals(parameters('network').mode, 'fresh')]")
        pe, integration = vnet["properties"]["subnets"]
        self.assertEqual(pe["properties"]["privateEndpointNetworkPolicies"], "Disabled")
        self.assertEqual(integration["properties"]["delegations"][0]["properties"]["serviceName"],
                         "Microsoft.Web/serverFarms")
        self.assertEqual(set(self.network["variables"]["zoneNames"]), set(foundation.ZONES.values()))
        for kind in ("Microsoft.Network/privateDnsZones", "Microsoft.Network/privateDnsZones/virtualNetworkLinks"):
            item, = resources(self.network, kind)
            self.assertEqual(item["condition"], "[variables('fresh')]")
        links, = resources(self.network, "Microsoft.Network/privateDnsZones/virtualNetworkLinks")
        self.assertFalse(links["properties"]["registrationEnabled"])
        mapping = self.main["definitions"]["privateNetworkConfiguration"]["discriminator"]["mapping"]
        self.assertEqual(set(mapping), {"fresh", "existing"})
        self.assertEqual(mapping["existing"]["properties"]["dnsLinksManagedExternally"]["allowedValues"], [True])
        self.assertIn("network').privateDnsZoneIds", self.network["outputs"]["privateDnsZoneResourceIds"]["value"])

    def test_issue147_profile_is_complete_and_external_network_put_conditions_are_false(self):
        profile = json.loads((ROOT / "infra/main.issue147-existing-network.parameters.json").read_text())
        supplied = set(profile["parameters"])
        self.assertFalse(supplied - set(self.main["parameters"]))
        required = {k for k, v in self.main["parameters"].items() if "defaultValue" not in v}
        self.assertFalse(required - supplied)
        self.assertTrue(foundation.validate_profile(profile)["offlineProfileValid"])
        values = {k: v["value"] for k, v in profile["parameters"].items()}
        self.assertEqual(values["network"]["mode"], "existing")
        self.assertTrue(values["network"]["dnsLinksManagedExternally"])
        self.assertEqual(values["keyVaultReferences"]["mode"], "existing")
        self.assertEqual(self.network["variables"]["fresh"], "[equals(parameters('network').mode, 'fresh')]")
        for item in resources(self.network):
            self.assertIn(item["type"], {
                "Microsoft.Network/virtualNetworks", "Microsoft.Network/privateDnsZones",
                "Microsoft.Network/privateDnsZones/virtualNetworkLinks"})
            self.assertIn(item["condition"], {
                "[equals(parameters('network').mode, 'fresh')]", "[variables('fresh')]"})
            # Both exact compiled expressions evaluate false for this real profile.
            self.assertFalse(values["network"]["mode"] == "fresh")
        for t in all_templates(self.main):
            self.assertFalse(resources(t, "Microsoft.Network/virtualNetworks/subnets"))

    def test_account_pe_three_zones_vault_and_storage_pe_groups(self):
        edges = module(self.main, "foundation-private-endpoints")
        targets = self.selected_vault_graph("freshVault")["targets"]
        account, vault = targets
        self.assertEqual(account["groupId"], "account")
        self.assertEqual(account["targetResourceId"], "new-foundry")
        self.assertEqual(len(account["privateDnsZoneResourceIds"]), 3)
        self.assertEqual(vault["groupId"], "vault")
        host_edges = module(self.function, "host-storage-private-endpoints")
        host_targets = host_edges["properties"]["parameters"]["targets"]["value"]
        self.assertEqual([x["groupId"] for x in host_targets], ["blob", "queue", "table"])
        self.assertTrue(all(len(x["privateDnsZoneResourceIds"]) == 1 for x in host_targets))
        for edge in (edges, host_edges):
            t = edge["properties"]["template"]
            endpoint, = resources(t, "Microsoft.Network/privateEndpoints")
            groups, = resources(t, "Microsoft.Network/privateEndpoints/privateDnsZoneGroups")
            self.assertNotIn("condition", endpoint)
            self.assertEqual(endpoint["properties"]["subnet"]["id"], "[parameters('subnetResourceId')]")
            configs, = groups["properties"]["copy"]
            self.assertEqual(configs["name"], "privateDnsZoneConfigs")
            self.assertEqual(configs["count"], "[length(parameters('targets')[copyIndex()].privateDnsZoneResourceIds)]")
            self.assertEqual(configs["input"]["properties"]["privateDnsZoneId"],
                             "[parameters('targets')[copyIndex()].privateDnsZoneResourceIds[copyIndex('privateDnsZoneConfigs')]]")
            self.assertNotIn("Microsoft.Network/privateDnsZones/A", {x["type"] for x in resources(t)})

    def selected_vault_graph(self, mode):
        references = {
            "modernFoundry": {"outputs": {"foundryAccountResourceId": {"value": "new-foundry"}}},
            "networking": {"outputs": {"privateDnsZoneResourceIds": {"value": foundation.ZONES}}},
        }
        if mode == "freshVault":
            references["keyVault"] = {"outputs": {
                "keyVaultResourceId": {"value": "new-vault"},
                "keyVaultName": {"value": "new-vault-name"}}}
        parameters = {"keyVaultReferences": {"mode": mode}}
        evaluate = lambda expression: evaluate_vault_expression(expression, parameters, references)
        vault = module(self.main, "key-vault-deployment")
        targets = module(self.main, "foundation-private-endpoints")["properties"]["parameters"]["targets"]["value"]
        return {"vaultCount": len(resources(vault["properties"]["template"], "Microsoft.KeyVault/vaults"))
                if evaluate(vault["condition"]) else 0,
                "targets": evaluate(targets), "evaluate": evaluate}

    def test_selected_existing_omits_owned_vault_and_endpoint_while_default_preserves_both(self):
        self.assertEqual(self.main["parameters"]["keyVaultReferences"]["defaultValue"], {"mode": "freshVault"})
        host_targets = module(self.function, "host-storage-private-endpoints")["properties"]["parameters"]["targets"]["value"]
        for mode, vault_count, pe_count, ip_count in (("freshVault", 1, 5, 7), ("existing", 0, 4, 6)):
            with self.subTest(mode=mode):
                graph = self.selected_vault_graph(mode)
                self.assertEqual(graph["vaultCount"], vault_count)
                groups = [target["groupId"] for target in graph["targets"] + host_targets]
                self.assertEqual(len(groups), pe_count)
                self.assertEqual(sum(3 if group == "account" else 1 for group in groups), ip_count)
                self.assertEqual("vault" in groups, mode == "freshVault")
                for output, expected in (("keyVaultResourceId", "new-vault"), ("keyVaultName", "new-vault-name")):
                    self.assertTrue(self.main["outputs"][output]["nullable"])
                    self.assertEqual(graph["evaluate"](self.main["outputs"][output]["value"]),
                                     expected if mode == "freshVault" else None)
                call = module(self.main, "function-app-deployment")["properties"]["parameters"]["keyVaultName"]
                self.assertEqual(graph["evaluate"](call)["value"], "new-vault-name" if mode == "freshVault" else None)
                reader = module(self.function, "function-fresh-vault-reader")
                self.assertEqual(graph["evaluate"](reader["condition"]), mode == "freshVault")
                self.assertEqual(graph["evaluate"](self.main["outputs"]["keyVaultReferenceMode"]["value"]), mode)
                self.assertEqual(graph["evaluate"](self.main["outputs"]["externalKeyVaultReferences"]["value"]),
                                 {"mode": "existing"} if mode == "existing" else None)

    def test_keyless_private_storage_vault_premium_and_outbound_integration(self):
        storage, = resources(self.function, "Microsoft.Storage/storageAccounts")
        self.assertFalse(storage["properties"]["allowSharedKeyAccess"])
        self.assertFalse(storage["properties"]["allowBlobPublicAccess"])
        self.assertEqual(storage["properties"]["publicNetworkAccess"], "Disabled")
        vault, = resources(child(self.main, "key-vault-deployment"), "Microsoft.KeyVault/vaults")
        self.assertEqual(vault["properties"]["publicNetworkAccess"], "Disabled")
        self.assertEqual(vault["properties"]["networkAcls"], {"defaultAction": "Deny", "bypass": "None"})
        for name in ("enableRbacAuthorization", "enableSoftDelete", "enablePurgeProtection"):
            self.assertTrue(vault["properties"][name])
        plan, = resources(self.function, "Microsoft.Web/serverfarms")
        self.assertEqual(plan["sku"], {"name": "EP1", "tier": "ElasticPremium", "capacity": 1})
        site, = resources(self.function, "Microsoft.Web/sites")
        self.assertEqual(site["properties"]["virtualNetworkSubnetId"],
                         "[parameters('functionIntegrationSubnetResourceId')]")
        self.assertTrue(site["properties"]["vnetRouteAllEnabled"])
        self.assertEqual(site["properties"]["publicNetworkAccess"], "Disabled")
        self.assertTrue(any("storagePrivateEndpoints" in x for x in site["dependsOn"]))
        for policy in resources(self.function, "Microsoft.Web/sites/basicPublishingCredentialsPolicies"):
            self.assertFalse(policy["properties"]["allow"])

    def test_keyless_bindings_consumer_package_and_disabled_runtime(self):
        settings = {x["name"]: x["value"] for x in self.function["variables"]["baseAppSettings"]}
        self.assertEqual(settings["AzureWebJobsStorage__credential"], "managedidentity")
        self.assertEqual(settings["EVENT_HUB_NAME"], "[parameters('eventHubName')]")
        self.assertEqual(settings["EVENT_HUB_CONSUMER_GROUP"], "[parameters('eventHubConsumerGroupName')]")
        self.assertEqual(settings["EVENT_HUB_CONNECTION_SETTING_PREFIX"],
                         "[parameters('eventHubConnectionSettingPrefix')]")
        for name in ("AzureWebJobs.TelemetryTransform.Disabled", "AzureWebJobs.DurableGenAIOutbox.Disabled"):
            self.assertEqual(settings[name], "true")
        self.assertIn("function-packages", settings["WEBSITE_RUN_FROM_PACKAGE"])
        self.assertEqual(settings["WEBSITE_RUN_FROM_PACKAGE_BLOB_MI_RESOURCE_ID"], "SystemAssigned")
        self.assertNotIn("WEBSITE_CONTENTAZUREFILECONNECTIONSTRING", settings)
        self.assertNotIn("AzureWebJobsStorage", settings)
        self.assertNotIn("DURABLE_GENAI_ENABLED", settings)
        call = module(self.main, "function-app-deployment")["properties"]["parameters"]
        self.assertIn("functionConsumerGroupName", call["eventHubConsumerGroupName"]["value"])
        self.assertTrue(call["prepareDurableGenAIContainer"]["value"])
        self.assertEqual({x["settingName"] for x in call["extraKeyVaultReferenceAppSettings"]["value"]},
                         {"ARIZE_OTLP_ENDPOINT", "ARIZE_SPACE_ID", "ARIZE_API_KEY"})

    def test_single_instance_bound_reaches_plan_and_app_with_explicit_warm_behavior(self):
        parameter = self.main["parameters"]["functionMaximumInstances"]
        self.assertEqual(parameter["allowedValues"], [1])
        self.assertEqual(parameter["defaultValue"], 1)
        call = module(self.main, "function-app-deployment")["properties"]["parameters"]
        self.assertEqual(call["maximumInstances"]["value"], "[parameters('functionMaximumInstances')]")
        self.assertEqual(self.function["parameters"]["maximumInstances"]["allowedValues"], [1])
        plan, = resources(self.function, "Microsoft.Web/serverfarms")
        self.assertEqual(plan["properties"]["maximumElasticWorkerCount"], "[parameters('maximumInstances')]")
        site, = resources(self.function, "Microsoft.Web/sites")
        config = site["properties"]["siteConfig"]
        self.assertEqual(config["functionAppScaleLimit"], "[parameters('maximumInstances')]")
        self.assertEqual(config["minimumElasticInstanceCount"], 1)
        self.assertEqual(config["preWarmedInstanceCount"], 1)
        for filename in ("main.parameters.json", "main.parameters.private-endpoint.json"):
            profile = json.loads((ROOT / "infra" / filename).read_text())
            self.assertEqual(profile["parameters"]["functionMaximumInstances"], {"value": 1})

    def test_existing_secret_references_are_forwarded_without_external_vault_writes_or_grants(self):
        call = module(self.main, "function-app-deployment")["properties"]["parameters"]
        self.assertEqual(call["keyVaultReferences"]["value"], "[parameters('keyVaultReferences')]")
        mapping = self.main["definitions"]["functionSecretReferences"]["discriminator"]["mapping"]
        self.assertEqual(set(mapping), {"freshVault", "existing"})
        self.assertEqual(set(mapping["existing"]["properties"]), {
            "mode", "applicationInsightsSecretUri", "arizeEndpointSecretUri",
            "arizeSpaceIdSecretUri", "arizeApiKeySecretUri"})
        reader = module(self.function, "function-fresh-vault-reader")
        self.assertEqual(reader["condition"], "[equals(parameters('keyVaultReferences').mode, 'freshVault')]")
        for field in ("arizeEndpointSecretUri", "arizeSpaceIdSecretUri", "arizeApiKeySecretUri"):
            self.assertIn(field, self.function["variables"]["extraAppSettings"])
        settings = {x["name"]: x["value"] for x in self.function["variables"]["baseAppSettings"]}
        self.assertIn("applicationInsightsSecretUri", settings["APPLICATIONINSIGHTS_CONNECTION_STRING"])
        access = compile_bicep("infra/existing-function-secret-access.bicep")
        self.assertEqual({r["type"] for r in resources(access)}, {"Microsoft.Authorization/roleAssignments"})
        role, = resources(access)
        self.assertIn("Microsoft.KeyVault/vaults/secrets", role["scope"])
        self.assertEqual(access["variables"]["secretsUserRoleId"], "4633458b-17de-408a-b874-0445c86b69e6")
        self.assertEqual(role["properties"]["principalId"], "[parameters('functionPrincipalId')]")

    def test_evaluated_function_vault_graph_with_null_owned_name_and_exact_fresh_rbac(self):
        reader = module(self.function, "function-fresh-vault-reader")
        inner = reader["properties"]["template"]
        self.assertEqual({r["type"] for r in resources(inner)}, {"Microsoft.Authorization/roleAssignments"})
        # ARM validates existing-resource names even if their consumer has a
        # false condition. Only a skipped nested deployment isolates that graph.
        for mode, vault_name in (("existing", None), ("freshVault", "synthetic-vault")):
            parameters = {"keyVaultReferences": {"mode": mode}, "keyVaultName": vault_name}
            evaluate = lambda expression: evaluate_vault_expression(expression, parameters, {})
            active = list(resources(self.function, writable=False))
            if evaluate(reader["condition"]):
                inner_parameters = {
                    "keyVaultName": evaluate(reader["properties"]["parameters"]["keyVaultName"]["value"]),
                    "functionAppResourceId": "/subscriptions/synthetic/resourceGroups/synthetic/providers/Microsoft.Web/sites/synthetic-function",
                    "functionPrincipalId": "synthetic-principal",
                }
                active += resources(inner, writable=False)
            else:
                inner_parameters = parameters
            evaluate_inner = lambda expression: evaluate_vault_expression(
                expression, inner_parameters,
                {"variables": inner.get("variables", {})})
            vaults = [r for r in active if r["type"] == "Microsoft.KeyVault/vaults"]
            for vault in vaults:
                self.assertIsInstance(evaluate_inner(vault["name"]), str)
            if mode == "existing":
                self.assertIsNone(parameters["keyVaultName"])
                self.assertFalse(any("keyVault" in r.get("scope", "") for r in active))
                continue
            role, = resources(inner, "Microsoft.Authorization/roleAssignments")
            legacy_vault_id = "/subscriptions/synthetic/resourceGroups/synthetic/providers/Microsoft.KeyVault/vaults/synthetic-vault"
            legacy_role_id = "4633458b-17de-408a-b874-0445c86b69e6"
            self.assertEqual(evaluate_inner(role["scope"]), legacy_vault_id)
            self.assertEqual(evaluate_inner(role["name"]), str(uuid.uuid5(
                uuid.UUID("11fb06fb-712d-4ddd-98c7-e71bbd588830"),
                "-".join((legacy_vault_id, inner_parameters["functionAppResourceId"], legacy_role_id)))))
            self.assertEqual(evaluate_inner(role["properties"]["roleDefinitionId"]),
                             "/subscriptions/synthetic/providers/Microsoft.Authorization/roleDefinitions/" + legacy_role_id)
            self.assertEqual(evaluate_inner(role["properties"]["principalId"]), "synthetic-principal")
            self.assertEqual(role["properties"]["principalType"], "ServicePrincipal")
            self.assertEqual(reader["properties"]["parameters"]["functionPrincipalId"]["value"],
                             "[reference('functionApp', '2023-12-01', 'full').identity.principalId]")

    def test_host_rbac_and_single_fresh_durable_export_ownership(self):
        self.assertEqual(set(self.function["variables"]["storageRoleIds"]), {
            "ba92f5b4-2d11-453d-a403-e96b0029c9fe", "974c5e8b-45b9-4653-ba55-5f855dd0fb88",
            "0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3", "b7e6dc6d-f1e8-4753-8033-0f276bb0955b",
        })
        t = child(self.main, "app-insights-deployment")
        export, = resources(t, "Microsoft.OperationalInsights/workspaces/dataExports")
        self.assertEqual(export["properties"], {
            "destination": {"resourceId": "[parameters('eventHubNamespaceResourceId')]",
                            "metaData": {"eventHubName": "[parameters('eventHubName')]"}},
            "tableNames": ["AppDependencies", "AppRequests", "AppGenAIContent"], "enable": True,
        })
        state = child(self.main, "fresh-durable-state")
        role, = resources(state, "Microsoft.Authorization/roleDefinitions")
        assignment, = resources(state, "Microsoft.Authorization/roleAssignments")
        self.assertEqual(role["properties"]["permissions"][0]["dataActions"], [
            "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/tags/write",
            "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/filter/action",
        ])
        self.assertIn("containers", assignment["scope"])
        self.assertIn("'durable-genai-index-v1'", role["name"])
        self.assertEqual(len([r for t in all_templates(self.main) for r in resources(t)
                              if r["type"].endswith("/dataExports")]), 1)
        self.assertEqual(len([r for r in resources(self.function) if r["type"].endswith("/containers")
                              and "genai-correlation" in r["name"]]), 1)

    def test_secure_tracing_across_boundaries_and_no_secret_outputs(self):
        for t in (self.main, child(self.main, "fresh-tracing-association")):
            self.assertEqual(t["parameters"]["appInsightsConnectionString"]["type"], "securestring")
            self.assertEqual(t["parameters"]["tracingAssociationMode"]["defaultValue"], "preserveExisting")
        tracing = module(self.main, "fresh-tracing-association")
        self.assertEqual(tracing["properties"]["parameters"]["appInsightsConnectionString"]["value"],
                         "[parameters('appInsightsConnectionString')]")
        for t in all_templates(self.main):
            for name, output in t.get("outputs", {}).items():
                if name == "connectionStringSecretUri":
                    continue  # URI is a reference identifier, not credential material.
                self.assertNotIn("ConnectionString", json.dumps(output.get("value", "")))
                self.assertNotIn("listKeys", json.dumps(output.get("value", "")))

    def test_issue147_bootstrap_uses_server_side_reference_and_secure_sink_only(self):
        bootstrap = compile_bicep("infra/issue147-app-insights-bootstrap.bicep")
        custody = module(bootstrap, "issue147-new-routing-custody")
        self.assertEqual(custody["resourceGroup"], "fotoa-demo-rg")
        call = custody["properties"]["parameters"]
        self.assertEqual(call["vaultName"]["value"], "fotoa-demo-kv-eastus2")
        self.assertEqual(call["secretName"]["value"], "fotoa147-appinsights-connection-string")
        self.assertIn("Microsoft.Insights/components", call["connectionString"]["value"])
        self.assertIn("fotoa147-demo-appi-eastus2", call["connectionString"]["value"])
        self.assertTrue(call["connectionString"]["value"].endswith(".ConnectionString]"))
        sink = custody["properties"]["template"]
        self.assertEqual(sink["parameters"]["connectionString"]["type"], "securestring")
        secret, = resources(sink)
        self.assertEqual(secret["type"], "Microsoft.KeyVault/vaults/secrets")
        self.assertEqual(secret["properties"]["value"], "[parameters('connectionString')]")
        self.assertIn("buildRequiredTags", json.dumps(secret["tags"]))
        self.assertEqual(set(sink["outputs"]), {"secretVersionUri", "componentBindingResourceId"})
        self.assertIn("secretUriWithVersion", sink["outputs"]["secretVersionUri"]["value"])
        self.assertEqual(set(bootstrap["outputs"]), set(sink["outputs"]))
        for template in all_templates(bootstrap):
            for output in template.get("outputs", {}).values():
                self.assertNotIn("ConnectionString", json.dumps(output))
                self.assertNotIn("connectionString", json.dumps(output))
        for old_secret in ("arize-otlp-endpoint", "arize-space-id", "arize-api-key"):
            self.assertNotIn(old_secret, json.dumps(bootstrap))
        self.assertNotIn("listSecrets", json.dumps(bootstrap))
        self.assertNotIn("Microsoft.Authorization/", json.dumps(bootstrap))

    def test_issue147_subscription_wrapper_binds_exact_profile_and_bootstrap_after_foundation(self):
        wrapper = compile_bicep("infra/issue147-first-allocation.bicep")
        self.assertIn("subscriptionDeploymentTemplate", wrapper["$schema"])
        self.assertFalse(wrapper.get("parameters"))
        group, = resources(wrapper, "Microsoft.Resources/resourceGroups")
        self.assertEqual(group["name"], "fotoa-demo-rg147-eastus2")
        foundation_call = module(wrapper, "issue147-fresh-application")
        bootstrap = module(wrapper, "issue147-routing-bootstrap")
        self.assertEqual(foundation_call["resourceGroup"], group["name"])
        self.assertEqual(bootstrap["resourceGroup"], group["name"])
        self.assertTrue(any("foundation" in dependency or "issue147-fresh-application" in dependency
                            for dependency in bootstrap["dependsOn"]))
        profile = json.loads((ROOT / "infra/main.issue147-existing-network.parameters.json").read_text())
        loaded = next(v for v in wrapper["variables"].values()
                      if isinstance(v, dict) and "parameters" in v)
        self.assertEqual(loaded["parameters"], profile["parameters"])
        actual = foundation_call["properties"]["parameters"]
        self.assertEqual(set(actual), set(profile["parameters"]))
        for name in actual:
            self.assertEqual(actual[name]["value"], f"[variables('p').{name}.value]")
        self.assertEqual(profile["parameters"]["tracingAssociationMode"]["value"], "preserveExisting")
        self.assertEqual(set(wrapper["outputs"]), {"secretVersionUri", "componentBindingResourceId"})

    def test_shared_naming_functions_and_portable_non_executable_profiles(self):
        tokens = self.function["variables"]["resourceTypeTokens"]
        self.assertEqual(tokens["foundryAccount"], "foundry")
        self.assertEqual(tokens["foundryProject"], "fproj")
        self.assertNotIn("foundryHub", tokens)
        for filename in ("main.parameters.json", "main.parameters.private-endpoint.json"):
            profile = json.loads((ROOT / "infra" / filename).read_text())
            with self.assertRaisesRegex(ValueError, "example/placeholders"):
                foundation.validate_profile(profile)
            serialized = json.dumps(profile)
            self.assertNotIn("fotoa-demo", serialized)
            self.assertNotIn("c81fda52", serialized)
            self.assertNotIn("appInsightsConnectionString", profile["parameters"])
        # Actual imported function bodies, not a comment/grep-only convention test.
        imported = self.function["functions"][0]["members"]
        self.assertIn("buildResourceName", imported)
        self.assertEqual(imported["buildResourceName"]["output"]["value"],
                         "[format('{0}-{1}-{2}-{3}', parameters('projectToken'), parameters('environment'), parameters('resourceType'), parameters('regionToken'))]")


def prepared_profile():
    values = {
        "projectToken": "sample", "environment": "dev", "location": "eastus2", "regionToken": "eus2",
        "ownerTag": "test-owner", "costCenterTag": "test-center",
        "accountName": "sample-dev-foundry-eus2", "projectName": "sample-dev-fproj-eus2",
        "customSubDomainName": "sample-dev-foundry-eus2", "modelDeploymentName": "chosen-alias",
        "modelFormat": "OpenAI", "modelName": "synthetic-catalog-selection", "modelVersion": "explicit-version",
        "modelDeploymentSkuName": "Standard", "modelDeploymentCapacity": 1,
        "modelVersionUpgradeOption": "NoAutoUpgrade", "modelDeploymentApproved": True,
        "modelDataResidencyApproval": "Test fixture only; regional processing approval",
        "network": {"mode": "fresh", "virtualNetworkAddressPrefix": "10.40.0.0/24",
                    "privateEndpointSubnetAddressPrefix": "10.40.0.0/26",
                    "functionIntegrationSubnetAddressPrefix": "10.40.0.64/26"},
        "functionPackageBlobName": "sha256-test-package.zip", "arizeProjectName": "test-project",
        "functionMaximumInstances": 1,
        "appInsightsConnectionName": "test-link",
    }
    return {"parameters": {k: {"value": v} for k, v in values.items()}}


class OfflineProfileTests(unittest.TestCase):
    def test_existing_secret_uris_reject_values_missing_fields_and_uri_injection(self):
        profile = prepared_profile()
        fields = ("applicationInsightsSecretUri", "arizeEndpointSecretUri",
                  "arizeSpaceIdSecretUri", "arizeApiKeySecretUri")
        refs = {"mode": "existing", **{
            key: f"https://sample-vault.vault.azure.net/secrets/test-{i}/"
            for i, key in enumerate(fields)}}
        profile["parameters"]["keyVaultReferences"] = {"value": refs}
        self.assertTrue(foundation.validate_profile(profile)["offlineProfileValid"])
        for bad in ("not-a-uri", "http://sample-vault.vault.azure.net/secrets/test/",
                    "https://x.vault.azure.net/secrets/test/",
                    "https://1vault.vault.azure.net/secrets/test/",
                    "https://sample--vault.vault.azure.net/secrets/test/",
                    "https://sample-vault.vault.azure.net.evil.test/secrets/test/",
                    "https://sample-vault.vault.azure.net/secrets/test/?sig=invalid",
                    "https://sample-vault.vault.azure.net/secrets/test/#fragment",
                    "https://sample-vault.vault.azure.net/secrets/test/invalid-version"):
            changed = copy.deepcopy(profile)
            changed["parameters"]["keyVaultReferences"]["value"][fields[0]] = bad
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, "four exact"):
                foundation.validate_profile(changed)
        for field in fields:
            changed = copy.deepcopy(profile)
            del changed["parameters"]["keyVaultReferences"]["value"][field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                foundation.validate_profile(changed)
        changed = copy.deepcopy(profile)
        changed["parameters"]["keyVaultReferences"]["value"][fields[0]] = refs[fields[1]]
        with self.assertRaisesRegex(ValueError, "distinct"):
            foundation.validate_profile(changed)

    def test_unbounded_or_larger_ep1_profile_rejected_before_provider(self):
        for value in (0, -1, 2, 20, True, "1", None):
            profile = prepared_profile()
            profile["parameters"]["functionMaximumInstances"]["value"] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "functionMaximumInstances=1"):
                foundation.validate_profile(profile)

    def test_complete_synthetic_profile_is_not_provider_or_runtime_proof(self):
        result = foundation.validate_profile(prepared_profile())
        self.assertTrue(result["offlineProfileValid"])
        self.assertFalse(result["providerValidated"])
        self.assertFalse(result["privateRuntimeVerified"])
        self.assertFalse(result["consumerEnabled"])
        self.assertFalse(result["tracingPutRequested"])

    def test_required_explicit_model_and_approval_inputs(self):
        for field in foundation.REQUIRED:
            profile = prepared_profile()
            del profile["parameters"][field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                foundation.validate_profile(profile)
        for field, value in (("modelVersion", ""), ("modelDeploymentCapacity", 0),
                             ("modelDeploymentCapacity", True), ("modelDeploymentApproved", False),
                             ("modelVersionUpgradeOption", "implicit"),
                             ("modelDataResidencyApproval", ""), ("projectToken", "TOO-LONG-TOKEN"),
                             ("functionPackageBlobName", "https://invalid.test/a.zip?sig=forbidden")):
            profile = prepared_profile()
            profile["parameters"][field]["value"] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                foundation.validate_profile(profile)

    def test_network_overlap_and_missing_ownership_rejected(self):
        for field, value in (("mode", "public"), ("functionIntegrationSubnetAddressPrefix", "10.40.0.0/26"),
                             ("functionIntegrationSubnetAddressPrefix", "10.40.1.0/26"),
                             ("functionIntegrationSubnetAddressPrefix", "10.40.0.64/28")):
            profile = prepared_profile()
            profile["parameters"]["network"]["value"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                foundation.validate_profile(profile)
        prefix = "/subscriptions/11111111-2222-3333-4444-555555555555/resourceGroups/test-network/providers/Microsoft.Network/"
        profile = prepared_profile()
        existing = {"mode": "existing", "privateEndpointSubnetResourceId": prefix + "virtualNetworks/test/subnets/pe",
                    "functionIntegrationSubnetResourceId": prefix + "virtualNetworks/test/subnets/integration",
                    "dnsLinksManagedExternally": True,
                    "privateDnsZoneIds": {k: prefix + "privateDnsZones/" + v for k, v in foundation.ZONES.items()}}
        profile["parameters"]["network"]["value"] = existing
        self.assertTrue(foundation.validate_profile(profile)["offlineProfileValid"])
        for key in existing:
            changed = copy.deepcopy(profile)
            del changed["parameters"]["network"]["value"][key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                foundation.validate_profile(changed)

    def test_active_tracing_requires_pinned_reference_and_review(self):
        profile = prepared_profile()
        profile["parameters"]["tracingAssociationMode"] = {"value": "ApiKey"}
        with self.assertRaises(ValueError):
            foundation.validate_profile(profile)
        profile["parameters"]["appInsightsConnectionPropertiesReviewed"] = {"value": True}
        profile["parameters"]["appInsightsConnectionString"] = {"reference": {
            "keyVault": {"id": "/subscriptions/11111111-2222-3333-4444-555555555555/resourceGroups/test-custody/providers/Microsoft.KeyVault/vaults/test-custody"},
            "secretName": "test-component-routing", "secretVersion": "a" * 32,
        }}
        self.assertTrue(foundation.validate_profile(profile)["tracingPutRequested"])
        for credential in ({"value": "FORBIDDEN"}, {"reference": {"secretName": "unpinned"}}):
            changed = copy.deepcopy(profile)
            changed["parameters"]["appInsightsConnectionString"] = credential
            with self.assertRaisesRegex(ValueError, "immutable Key Vault"):
                foundation.validate_profile(changed)


if __name__ == "__main__":
    unittest.main()
