"""Offline compiled contracts: preparation must not enable content/export or grants."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest


@pytest.fixture(scope="module")
def compiled_function_module():
    root = Path(__file__).resolve().parents[3]
    az = shutil.which("az")
    if az is None:
        pytest.skip("Azure CLI/Bicep required for compiled infrastructure contract")
    result = subprocess.run(
        [az, "bicep", "build", "--file", str(root / "infra" / "modules" / "function-app.bicep"),
         "--stdout", "--only-show-errors"],
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
    assert len(containers) == 1
    container = containers[0]
    assert container["condition"] == "[parameters('prepareDurableGenAIContainer')]"
    assert container["properties"]["publicAccess"] == "None"
    assert container["name"] == (
        "[format('{0}/{1}/{2}', variables('storageAccountName'), 'default', 'genai-correlation')]"
    )
    serialized = json.dumps(template)
    assert "DURABLE_GENAI_ENABLED" not in serialized
    assert "AppGenAIContent" not in serialized
    assert "Microsoft.OperationalInsights/workspaces/dataExports" not in serialized


def test_preparation_retains_existing_role_inventory_only(compiled_function_module):
    resources = compiled_function_module["resources"]
    if isinstance(resources, dict):
        resources = list(resources.values())
    roles = [item for item in resources if item["type"] == "Microsoft.Authorization/roleAssignments"]
    assert len(roles) == 5
    # Existing Function host Blob/Queue/Table, Event Hub receiver and Key Vault reader.
    existing_roles = {
        "ba92f5b4-2d11-453d-a403-e96b0029c9fe",
        "974c5e8b-45b9-4653-ba55-5f855dd0fb88",
        "0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3",
        "a638d3c7-ab3a-418d-83e6-5f17a39d4fde",
        "4633458b-17de-408a-b874-0445c86b69e6",
    }
    variables = compiled_function_module.get("variables", {})
    encoded = json.dumps(variables) + json.dumps(roles)
    assert all(role in encoded for role in existing_roles)
