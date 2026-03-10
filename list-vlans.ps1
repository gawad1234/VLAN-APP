<#
.SYNOPSIS
  List VLAN-related network adapter properties on Windows.

.DESCRIPTION
  This script queries Windows networking stack (via Get-NetAdapter and
  Get-NetAdapterAdvancedProperty) and prints any VLAN-related advanced properties
  exposed by NIC drivers.

.EXAMPLE
  .\list-vlans.ps1
#>

function Get-VlanAdapterInfo {
    $adapters = Get-NetAdapter | Select-Object Name,InterfaceDescription,Status,MacAddress,InterfaceIndex

    $vlanProps = Get-NetAdapterAdvancedProperty | Where-Object {
        $_.DisplayName -match 'Vlan|VLAN|vlan' -or $_.RegistryKeyword -match 'Vlan|VLAN|vlan'
    } | Select-Object Name,DisplayName,RegistryKeyword,RegistryValue,InterfaceIndex

    $map = @{}
    foreach ($p in $vlanProps) {
        $key = $p.InterfaceIndex
        if (-not $key) { $key = $p.Name }
        $map[$key] = ($map[$key] + @("$($p.DisplayName): $($p.RegistryValue)"))
    }

    foreach ($a in $adapters) {
        $vlan = $map[$a.InterfaceIndex]
        if (-not $vlan) { $vlan = @('(none found)') }

        [PSCustomObject]@{
            Name = $a.Name
            Description = $a.InterfaceDescription
            Status = $a.Status
            MAC = $a.MacAddress
            'VLAN Properties' = $vlan -join '; '
        }
    }
}

Get-VlanAdapterInfo | Format-Table -AutoSize
