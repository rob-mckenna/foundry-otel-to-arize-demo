"""Bounded read-only #153 metadata. Never emit settings, credentials or raw errors."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parents[1]
SUB = "c81fda52-936e-4f14-8af4-951c0dbb92d2"
R = f"/subscriptions/{SUB}/resourceGroups/fotoa-demo-rg"
F = R + "/providers/Microsoft.Web/sites/fotoa-demo-func-eastus2"
LAW = R + "/providers/Microsoft.OperationalInsights/workspaces/fotoa-demo-law-eastus2"
GOV = (f"/subscriptions/{SUB}/resourceGroups/McapsGovernance/providers/"
       "Microsoft.OperationalInsights/workspaces/mcaps4f148af4951c0dbb92d2-la")
ENV = dict(os.environ, AZURE_CONFIG_DIR=str(REPO / ".azure-config"),
           AZURE_EXTENSION_USE_DYNAMIC_INSTALL="no",
           AZURE_CORE_COLLECT_TELEMETRY="no")
AZ = shutil.which("az")
RESULTS = {}


def read(label, arguments, query=None):
    args = [AZ, *arguments, "--subscription", SUB, "--only-show-errors", "-o", "json"]
    if query:
        args.extend(["--query", query])
    try:
        p = subprocess.run(args, env=ENV, capture_output=True, text=True, timeout=120)
        if p.returncode:
            codes = sorted(set(re.findall(
                r"\b(?:AuthorizationFailed|Forbidden|ResourceNotFound|NotFound|"
                r"AuthenticationFailed|InvalidAuthenticationTokenTenant|"
                r"ConnectionError|BadRequest|ContainerNotFound|ResourceGroupNotFound|403|401|404)\b", p.stderr)))[:4]
            result = {"status": "FAILED", "exit": p.returncode, "safeCodes": codes or ["Unclassified"]}
        else:
            result = {"status": "OK", "metadata": json.loads(p.stdout)}
    except (subprocess.TimeoutExpired, OSError, ValueError):
        result = {"status": "FAILED", "safeCodes": ["InvocationOrDecodeFailure"]}
    RESULTS[label] = result
    print(json.dumps({label: result}))
    return result


def rest(label, resource, api, query):
    return read(label, ["rest", "--method", "get", "--url",
                       f"https://management.azure.com{resource}?api-version={api}"], query)


def main():
    rest("function", F, "2023-12-01",
         "{id:id,identity:identity.principalId,state:properties.state,kind:kind,"
         "publicNetworkAccess:properties.publicNetworkAccess}")
    rest("linuxRuntime", F + "/config/web", "2023-12-01",
         "{linuxFxVersion:properties.linuxFxVersion,scmIpSecurityRestrictionsDefaultAction:"
         "properties.scmIpSecurityRestrictionsDefaultAction,vnetRouteAllEnabled:properties.vnetRouteAllEnabled,"
         "scmUsesMainRestrictions:properties.scmIpSecurityRestrictionsUseMain,"
         "scmRules:properties.scmIpSecurityRestrictions[].{name:name,action:action,priority:priority},"
         "mainRules:properties.ipSecurityRestrictions[].{name:name,action:action,priority:priority}}")
    rest("functionDeployments", F + "/deployments", "2023-12-01",
         "value[].{id:name,status:properties.status,active:properties.active,"
         "start:properties.start_time,end:properties.end_time}")
    read("settingsEnums", ["functionapp", "config", "appsettings", "list",
                          "-g", "fotoa-demo-rg", "-n", "fotoa-demo-func-eastus2"],
         "{monitoringPresent:length([?name=='APPLICATIONINSIGHTS_CONNECTION_STRING'])==`1`,"
         "monitoringKV:length([?name=='APPLICATIONINSIGHTS_CONNECTION_STRING' && starts_with(value,'@Microsoft.KeyVault(')])==`1`,"
         "legacyKeyPresent:length([?name=='APPINSIGHTS_INSTRUMENTATIONKEY'])==`1`,"
         "packagePresent:length([?name=='WEBSITE_RUN_FROM_PACKAGE'])==`1`,"
         "packageLocal:length([?name=='WEBSITE_RUN_FROM_PACKAGE' && value=='1'])==`1`,"
         "packageBlob:length([?name=='WEBSITE_RUN_FROM_PACKAGE' && starts_with(value,'https://')])==`1`,"
         "incomingDisabled:length([?name=='AzureWebJobs.TelemetryTransform.Disabled' && (value=='true' || value=='1')])==`1`,"
         "outboxDisabled:length([?name=='AzureWebJobs.DurableGenAIOutbox.Disabled' && (value=='true' || value=='1')])==`1`,"
         "durableEnabled:length([?name=='DURABLE_GENAI_ENABLED' && (value=='true' || value=='1')])==`1`,"
         "workspaceScopeMatches:length([?name=='DURABLE_ALLOWED_WORKSPACE_ID' && value=='4658bdb1-b9ca-4f57-a733-6b81f316dc45'])==`1`,"
         "componentScopeMatches:length([?name=='DURABLE_ALLOWED_COMPONENT_RESOURCE_ID' && value=='" +
         R + "/providers/Microsoft.Insights/components/fotoa-demo-appi-eastus2'])==`1`}")
    rest("agentComponent", R + "/providers/Microsoft.Insights/components/fotoa-demo-appi-eastus2",
         "2020-02-02", "{id:id,workspace:properties.WorkspaceResourceId}")
    rest("agentWorkspace", LAW, "2023-09-01",
         "{id:id,customerId:properties.customerId,sku:properties.sku.name,"
         "retention:properties.retentionInDays,cap:properties.workspaceCapping.dailyQuotaGb}")
    rest("sourceExports", LAW + "/dataExports", "2020-08-01",
         "value[].{name:name,enabled:properties.enable,tables:properties.tableNames,destination:properties.destination}")
    rest("functionDiagnostics", F + "/providers/Microsoft.Insights/diagnosticSettings",
         "2021-05-01-preview", "value[].{name:name,workspaceId:properties.workspaceId,"
         "eventHubAuthorizationRuleId:properties.eventHubAuthorizationRuleId,"
         "eventHubName:properties.eventHubName,storageAccountId:properties.storageAccountId}")
    rest("governanceDataExports", GOV + "/dataExports", "2020-08-01",
         "value[].{name:name,enabled:properties.enable,destination:properties.destination}")
    rest("governanceDiagnostics", GOV + "/providers/Microsoft.Insights/diagnosticSettings",
         "2021-05-01-preview", "value[].{name:name,workspaceId:properties.workspaceId,"
         "eventHubAuthorizationRuleId:properties.eventHubAuthorizationRuleId,"
         "eventHubName:properties.eventHubName,storageAccountId:properties.storageAccountId}")
    rest("storage", R + "/providers/Microsoft.Storage/storageAccounts/fotoademosteastus2",
         "2023-05-01", "{id:id,publicNetworkAccess:properties.publicNetworkAccess,"
         "defaultAction:properties.networkAcls.defaultAction,privateEndpoints:"
         "properties.privateEndpointConnections[].properties.privateLinkServiceConnectionState.status}")
    rest("packageContainer", R + "/providers/Microsoft.Storage/storageAccounts/fotoademosteastus2/"
         "blobServices/default/containers/function-packages", "2023-05-01",
         "{id:id,publicAccess:properties.publicAccess}")
    vm = R + "/providers/Microsoft.Compute/virtualMachines/fotoa-validation-vm-eastus2"
    rest("validationVM", vm, "2024-03-01",
         "{id:id,principalId:identity.principalId,size:properties.hardwareProfile.vmSize}")
    rest("validationVMState", vm + "/instanceView", "2024-03-01", "statuses[].code")
    rest("deploymentHistory", R + "/providers/Microsoft.Resources/deployments",
         "2022-09-01", "value[].{name:name,state:properties.provisioningState,timestamp:properties.timestamp}")
    output = ROOT / ".release/baseline-metadata.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(RESULTS, indent=2) + "\n")


if __name__ == "__main__":
    main()
