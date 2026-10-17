"""One-page, allowlisted ARM association readback; no credential endpoints or raw errors."""

import argparse
import json
import re
import shutil
import subprocess
import sys


SUBSCRIPTION = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
SEGMENT = r"[a-zA-Z0-9_.()-]+"
PROJECT_ID = re.compile(
    rf"/subscriptions/{SUBSCRIPTION}/resourceGroups/{SEGMENT}"
    rf"/providers/Microsoft\.CognitiveServices/accounts/{SEGMENT}/projects/{SEGMENT}",
    re.IGNORECASE,
)
APP_INSIGHTS_ID = re.compile(
    rf"/subscriptions/{SUBSCRIPTION}/resourceGroups/{SEGMENT}"
    rf"/providers/Microsoft\.Insights/components/{SEGMENT}",
    re.IGNORECASE,
)
CONNECTION_NAME = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{2,32}")
PROJECTION = (
    "{connections:value[?properties.category=='AppInsights']."
    "{id:id,name:name,category:properties.category,target:properties.target,"
    "authType:properties.authType,resourceId:properties.metadata.ResourceId,"
    "isSharedToAll:properties.isSharedToAll},"
    "hasNext:nextLink}"
)


def validate_inputs(project_id, connection_name, target_id):
    if not PROJECT_ID.fullmatch(project_id):
        raise ValueError("Expected an exact modern Foundry project ARM ID.")
    if not CONNECTION_NAME.fullmatch(connection_name):
        raise ValueError("Expected a 3-33 character connection name.")
    if not APP_INSIGHTS_ID.fullmatch(target_id):
        raise ValueError("Expected an exact Application Insights component ARM ID.")


def validate_association(document, project_id, connection_name, target_id, auth_type, expected_sharing=None):
    validate_inputs(project_id, connection_name, target_id)
    if auth_type not in {"ApiKey", "ProjectManagedIdentity"}:
        raise ValueError("Expected ApiKey or ProjectManagedIdentity authentication.")
    if not isinstance(document, dict):
        raise ValueError("Association readback must be a projected JSON object.")
    if document.get("hasNext"):
        raise ValueError("Incomplete connection inventory: pagination is not accepted.")
    connections = document.get("connections")
    if not isinstance(connections, list) or len(connections) != 1:
        raise ValueError("Expected exactly one AppInsights connection; missing or duplicate association.")
    connection = connections[0]
    if not isinstance(connection, dict):
        raise ValueError("Association readback must contain a projected connection object.")
    expected = {
        "id": f"{project_id}/connections/{connection_name}",
        "name": connection_name,
        "category": "AppInsights",
        "target": target_id,
        "resourceId": target_id,
        "authType": auth_type,
    }
    for field, value in expected.items():
        actual = connection.get(field)
        # ARM IDs/names are case insensitive; category and auth discriminators are not.
        equal = (
            isinstance(actual, str) and actual.casefold() == value.casefold()
            if field in {"id", "name", "target", "resourceId"}
            else actual == value
        )
        if not equal:
            raise ValueError(f"AppInsights association mismatch in {field}; no values emitted.")
    if expected_sharing is not None:
        if expected_sharing not in {"private", "projectShared"}:
            raise ValueError("Expected sharing must be private or projectShared.")
        if connection.get("isSharedToAll") is not (expected_sharing == "projectShared"):
            raise ValueError("AppInsights association mismatch in isSharedToAll; no values emitted.")
    return {
        "associationVerified": True,
        "connectionResourceId": expected["id"],
        "category": "AppInsights",
        "targetResourceId": target_id,
        "authType": auth_type,
        "sharingVerified": expected_sharing is not None,
        "traceDeliveryVerified": False,
    }


def read_association(project_id, connection_name, target_id, auth_type, expected_sharing=None):
    validate_inputs(project_id, connection_name, target_id)
    cli = shutil.which("az")
    if not cli:
        raise ValueError("Azure CLI is unavailable.")
    # Explicit subscription; no account switch, POST/listSecrets, retries or pagination.
    command = [
        cli, "rest", "--method", "get",
        "--url", f"https://management.azure.com{project_id}/connections?api-version=2025-09-01",
        "--subscription", project_id.split("/")[2],
        "--query", PROJECTION, "--output", "json", "--only-show-errors",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=90, check=False)
    except subprocess.TimeoutExpired:
        raise ValueError("Association readback timed out after 90 seconds; not verified.") from None
    if result.returncode:
        raise ValueError("ARM association readback failed; not verified. Raw CLI errors suppressed.")
    try:
        document = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise ValueError("Association readback returned invalid JSON; not verified.") from None
    return validate_association(document, project_id, connection_name, target_id, auth_type, expected_sharing)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-resource-id", required=True)
    parser.add_argument("--connection-name", required=True)
    parser.add_argument("--app-insights-resource-id", required=True)
    parser.add_argument("--expected-auth-type", choices=["ApiKey", "ProjectManagedIdentity"], required=True)
    parser.add_argument("--expected-sharing", choices=["private", "projectShared"])
    args = parser.parse_args()
    try:
        receipt = read_association(
            args.project_resource_id, args.connection_name,
            args.app_insights_resource_id, args.expected_auth_type,
            args.expected_sharing,
        )
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1
    except OSError:
        print("Association CLI could not execute; not verified.", file=sys.stderr)
        return 1
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
