"""Offline compiled contracts for baseline preparation and the narrow opt-in rollout."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest


@pytest.fixture(scope="module")
def compiled_function_module():
    root = Path(__file__).resolve().parents[3]
    bicep = os.environ.get("BICEP_CLI") or shutil.which("bicep")
    az = shutil.which("az") if not bicep else None
    if bicep is None and az is None:
        pytest.skip("Azure CLI/Bicep required for compiled infrastructure contract")
    result = subprocess.run(
        ([bicep, "build", str(root / "infra" / "modules" / "function-app.bicep"), "--stdout"] if bicep else
         [az, "bicep", "build", "--file", str(root / "infra" / "modules" / "function-app.bicep"),
          "--stdout", "--only-show-errors"]),
        capture_output=True, text=True, timeout=120, check=False,
    )
    assert result.returncode == 0, "Offline Bicep compilation failed"
    return json.loads(result.stdout)


def test_container_is_private_opt_in_without_runtime_or_export_enablement(compiled_function_module):
    template = compiled_function_module
    assert template["parameters"]["prepareDurableGenAIContainer"]["defaultValue"] is False
    resources = template["resources"]
    if isinstance(resources, dict):
        resources = list(resources.values())
    containers = [item for item in resources if item["type"].endswith("/blobServices/containers")]
    assert len(containers) == 2
    # Modern keyless Premium adds a separate private deployment-package container.
    container = next(item for item in containers if "genai-correlation" in item["name"])
    assert container["condition"] == "[parameters('prepareDurableGenAIContainer')]"
    assert container["properties"]["publicAccess"] == "None"
    assert container["name"] == (
        "[format('{0}/{1}/{2}', variables('storageAccountName'), 'default', 'genai-correlation')]"
    )
    serialized = json.dumps(template)
    assert "DURABLE_GENAI_ENABLED" not in serialized
    assert "AppGenAIContent" not in serialized
    assert "Microsoft.OperationalInsights/workspaces/dataExports" not in serialized


def test_preparation_retains_roles_and_adds_required_keyless_host_owner(compiled_function_module):
    resources = compiled_function_module["resources"]
    if isinstance(resources, dict):
        resources = list(resources.values())
    roles = [item for item in resources if item["type"] == "Microsoft.Authorization/roleAssignments"]
    assert len(roles) == 3  # four host roles in one ARM copy, plus EH and KV assignments
    # Retained Blob/Queue/Table, EH receiver and KV reader, plus host Blob Data Owner.
    existing_roles = {
        "ba92f5b4-2d11-453d-a403-e96b0029c9fe",
        "974c5e8b-45b9-4653-ba55-5f855dd0fb88",
        "0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3",
        "a638d3c7-ab3a-418d-83e6-5f17a39d4fde",
        "4633458b-17de-408a-b874-0445c86b69e6",
        "b7e6dc6d-f1e8-4753-8033-0f276bb0955b",
    }
    variables = compiled_function_module.get("variables", {})
    encoded = json.dumps(variables) + json.dumps(roles)
    assert all(role in encoded for role in existing_roles)


@pytest.fixture(scope="module")
def compiled_durable_rollout():
    root = Path(__file__).resolve().parents[3]
    bicep = os.environ.get("BICEP_CLI") or shutil.which("bicep")
    az = shutil.which("az") if not bicep else None
    if bicep is None and az is None:
        pytest.skip("Azure CLI/Bicep required for compiled infrastructure contract")
    result = subprocess.run(
        ([bicep, "build", str(root / "infra" / "durable-genai-rollout.bicep"), "--stdout"] if bicep else
         [az, "bicep", "build", "--file", str(root / "infra" / "durable-genai-rollout.bicep"),
          "--stdout", "--only-show-errors"]),
        capture_output=True, text=True, timeout=120, check=False,
    )
    assert result.returncode == 0, "Offline rollout Bicep compilation failed"
    return json.loads(result.stdout)


def _resources_by_type(template):
    resources = template["resources"]
    if isinstance(resources, dict):
        resources = list(resources.values())
    return {item["type"]: item for item in resources if not item.get("existing", False)}


def test_rollout_writes_only_private_container_index_rbac_and_existing_export(compiled_durable_rollout):
    template = compiled_durable_rollout
    resources = _resources_by_type(template)
    assert len(resources) == 4
    assert set(resources) == {
        "Microsoft.Storage/storageAccounts/blobServices/containers",
        "Microsoft.Authorization/roleDefinitions",
        "Microsoft.Authorization/roleAssignments",
        "Microsoft.OperationalInsights/workspaces/dataExports",
    }
    container = resources["Microsoft.Storage/storageAccounts/blobServices/containers"]
    assert container["properties"] == {"publicAccess": "None"}
    assert container["name"] == (
        "[format('{0}/{1}/{2}', parameters('storageAccountName'), 'default', 'genai-correlation')]"
    )
    assert "DURABLE_GENAI_ENABLED" not in json.dumps(template)


def test_rollout_role_is_additive_two_action_rg_definition_container_assignment(compiled_durable_rollout):
    resources = _resources_by_type(compiled_durable_rollout)
    role = resources["Microsoft.Authorization/roleDefinitions"]
    assert role.get("scope") is None
    assert role["properties"]["type"] == "CustomRole"
    assert role["properties"]["assignableScopes"] == ["[resourceGroup().id]"]
    assert role["properties"]["permissions"] == [{
        "actions": [],
        "notActions": [],
        "dataActions": [
            "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/tags/write",
            "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/filter/action",
        ],
        "notDataActions": [],
    }]
    assignment = resources["Microsoft.Authorization/roleAssignments"]
    assert assignment["scope"] == (
        "[resourceId('Microsoft.Storage/storageAccounts/blobServices/containers', "
        "parameters('storageAccountName'), 'default', 'genai-correlation')]"
    )
    assert assignment["properties"]["principalId"] == "[parameters('functionPrincipalId')]"
    assert assignment["properties"]["principalType"] == "ServicePrincipal"
    assert assignment["properties"]["roleDefinitionId"].startswith(
        "[resourceId('Microsoft.Authorization/roleDefinitions', "
    )
    assert "guid(" in role["name"] and "guid(" in assignment["name"]


def test_rollout_preserves_complete_export_snapshot_and_requires_explicit_targets(compiled_durable_rollout):
    template = compiled_durable_rollout
    parameters = template["parameters"]
    assert all("defaultValue" not in value for value in parameters.values())
    export = _resources_by_type(template)["Microsoft.OperationalInsights/workspaces/dataExports"]
    assert export["name"] == (
        "[format('{0}/{1}', parameters('workspaceName'), parameters('exportRuleName'))]"
    )
    assert export["properties"] == {
        "destination": {
            "resourceId": "[parameters('eventHubNamespaceResourceId')]",
            "metaData": {"eventHubName": "[parameters('eventHubName')]"},
        },
        "tableNames": (
            "[union(parameters('existingExportTableNames'), "
            "createArray('AppDependencies', 'AppRequests', 'AppGenAIContent'))]"
        ),
        "enable": "[parameters('existingExportEnabled')]",
    }
