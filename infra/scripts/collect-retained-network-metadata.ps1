<#
.SYNOPSIS
Read-only, fixed-scope metadata evidence for issue 148. Never executes cleanup.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $OutputPath
)
$ErrorActionPreference = 'Stop'
$subscription = 'c81fda52-936e-4f14-8af4-951c0dbb92d2'
$rg = "/subscriptions/$subscription/resourceGroups/fotoa-demo-rg"
$network = "$rg/providers/Microsoft.Network"
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$destination = [IO.Path]::GetFullPath((Join-Path $root $OutputPath))
if (-not $destination.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Output must be inside this worktree.'
}
if (Test-Path $destination) { throw 'Evidence already exists; use a new filename.' }
$env:AZURE_CONFIG_DIR = 'C:\repos\foundry-otel-to-arize-demo\.azure-config'

function Read-Metadata([string] $Path, [string] $Query) {
    $started = [DateTime]::UtcNow.ToString('o')
    $oldPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $raw = & az rest --method get --url "https://management.azure.com$Path" `
            --subscription $subscription --query $Query --output json --only-show-errors
        $code = $LASTEXITCODE
    } finally { $ErrorActionPreference = $oldPreference }
    if ($code -ne 0) { throw "Metadata GET failed ($code): $Path" }
    $result = ($raw -join "`n") | ConvertFrom-Json
    if ($result.PSObject.Properties['nextLink'] -and $result.nextLink) {
        throw "Incomplete metadata collection: $Path"
    }
    [pscustomobject]@{ startedUtc = $started; path = $Path; query = $Query; data = $result }
}

$evidence = [ordered]@{
    schemaVersion = 1
    issue = 148
    mode = 'READ_ONLY_METADATA_NO_AUTHORIZATION'
    startedUtc = [DateTime]::UtcNow.ToString('o')
    subscriptionId = $subscription
    resourceGroupId = $rg
}
$evidence.resources = Read-Metadata "$rg/resources?api-version=2021-04-01" `
    '{nextLink:nextLink,items:value[].{id:id,type:type,kind:kind,location:location,managedBy:managedBy}}'
$evidence.endpoints = Read-Metadata "$network/privateEndpoints?api-version=2023-11-01" `
    '{nextLink:nextLink,items:value[].{id:id,type:type,managedBy:managedBy,state:properties.provisioningState,subnetId:properties.subnet.id,nics:properties.networkInterfaces[].id,connections:properties.privateLinkServiceConnections[].{id:id,target:properties.privateLinkServiceId,groups:properties.groupIds,status:properties.privateLinkServiceConnectionState.status},manual:properties.manualPrivateLinkServiceConnections[].{id:id,target:properties.privateLinkServiceId,groups:properties.groupIds,status:properties.privateLinkServiceConnectionState.status}}}'
$evidence.nics = Read-Metadata "$network/networkInterfaces?api-version=2023-11-01" `
    '{nextLink:nextLink,items:value[].{id:id,type:type,managedBy:managedBy,state:properties.provisioningState,privateEndpointId:properties.privateEndpoint.id,virtualMachineId:properties.virtualMachine.id,nsgId:properties.networkSecurityGroup.id,ipConfigurations:properties.ipConfigurations[].{id:id,privateIPAddress:properties.privateIPAddress,subnetId:properties.subnet.id,publicIPAddressId:properties.publicIPAddress.id,loadBalancerBackendAddressPools:properties.loadBalancerBackendAddressPools[].id,loadBalancerInboundNatRules:properties.loadBalancerInboundNatRules[].id,applicationGatewayBackendAddressPools:properties.applicationGatewayBackendAddressPools[].id,applicationSecurityGroups:properties.applicationSecurityGroups[].id}}}'
$evidence.vnets = Read-Metadata "$network/virtualNetworks?api-version=2023-11-01" `
    '{nextLink:nextLink,items:value[].{id:id,state:properties.provisioningState,subnets:properties.subnets[].{id:id,nsgId:properties.networkSecurityGroup.id,routeTableId:properties.routeTable.id,natGatewayId:properties.natGateway.id,privateEndpoints:properties.privateEndpoints[].id,ipConfigurations:properties.ipConfigurations[].id,delegations:properties.delegations[].properties.serviceName}}}'
$evidence.dnsGroups = @(
    foreach ($pe in $evidence.endpoints.data.items) {
        Read-Metadata "$($pe.id)/privateDnsZoneGroups?api-version=2023-11-01" `
            '{nextLink:nextLink,items:value[].{id:id,state:properties.provisioningState,configs:properties.privateDnsZoneConfigs[].{id:properties.privateDnsZoneId,recordSets:properties.recordSets[].{name:recordSetName,type:recordType,ttl:ttl,ipAddresses:ipAddresses}}}}'
    }
)
$evidence.zones = Read-Metadata "$network/privateDnsZones?api-version=2020-06-01" `
    '{nextLink:nextLink,items:value[].{id:id,type:type,recordSetCount:properties.numberOfRecordSets,linkCount:properties.numberOfVirtualNetworkLinks}}'
$evidence.dns = @(
    foreach ($zone in $evidence.zones.data.items) {
        [pscustomobject]@{
            zoneId = $zone.id
            records = Read-Metadata "$($zone.id)/ALL?api-version=2020-06-01" `
                '{nextLink:nextLink,items:value[].{id:id,type:type,ttl:properties.ttl,aRecords:properties.aRecords[].ipv4Address,cnameRecord:properties.cnameRecord.cname}}'
            links = Read-Metadata "$($zone.id)/virtualNetworkLinks?api-version=2020-06-01" `
                '{nextLink:nextLink,items:value[].{id:id,vnetId:properties.virtualNetwork.id,registrationEnabled:properties.registrationEnabled,state:properties.virtualNetworkLinkState}}'
        }
    }
)
$evidence.roles = Read-Metadata "$rg/providers/Microsoft.Authorization/roleAssignments?api-version=2022-04-01" `
    '{nextLink:nextLink,items:value[].{id:id,type:type,scope:properties.scope,principalId:properties.principalId,roleDefinitionId:properties.roleDefinitionId}}'
$evidence.locks = Read-Metadata "$rg/providers/Microsoft.Authorization/locks?api-version=2016-09-01" `
    '{nextLink:nextLink,items:value[].{id:id,level:properties.level}}'
$evidence.protectedChildren = @(
    Read-Metadata "$rg/providers/Microsoft.CognitiveServices/accounts/fotoa-demo-foundry-eastus2/projects/fotoa-demo-fproj-eastus2?api-version=2025-06-01" `
        '{id:id,type:type,location:location,provisioningState:properties.provisioningState,principalId:identity.principalId}'
    Read-Metadata "$rg/providers/Microsoft.EventHub/namespaces/fotoa-demo-ehns-eastus2/eventhubs/telemetry/consumergroups/function-transform?api-version=2024-01-01" `
        '{id:id,type:type,name:name}'
    Read-Metadata "$rg/providers/Microsoft.Storage/storageAccounts/fotoademosteastus2/blobServices/default/containers?api-version=2023-05-01" `
        '{nextLink:nextLink,items:value[].{id:id,name:name,type:type}}'
    Read-Metadata "$rg/providers/Microsoft.Compute/virtualMachines/fotoa-validation-vm-eastus2/instanceView?api-version=2024-07-01" `
        '{powerState:statuses[?starts_with(code, `PowerState/`)].code}'
)
$evidence.completedUtc = [DateTime]::UtcNow.ToString('o')
[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destination)) | Out-Null
[IO.File]::WriteAllText($destination, ($evidence | ConvertTo-Json -Depth 35),
    [Text.UTF8Encoding]::new($false))
Write-Output "Metadata evidence written: $destination"
