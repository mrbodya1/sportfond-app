# Read-only diagnostic snapshot. Run as Administrator when the owner returns.
$ErrorActionPreference = 'Stop'
$principal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run from PowerShell as Administrator.'
}
$folder = Join-Path $env:ProgramData ('Sportfond\network-diagnostics\' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
[void](New-Item -ItemType Directory -Path $folder)
Get-NetIPAddress -AddressFamily IPv4 | Select-Object InterfaceAlias,IPAddress,PrefixLength |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $folder 'addresses.json') -Encoding utf8
Get-NetRoute -AddressFamily IPv4 | Select-Object InterfaceAlias,DestinationPrefix,NextHop,RouteMetric |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $folder 'routes.json') -Encoding utf8
Get-NetFirewallRule -PolicyStore ActiveStore -Enabled True |
    Select-Object DisplayName,Direction,Action,Profile |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $folder 'firewall.json') -Encoding utf8
& netsh wfp show filters "file=$(Join-Path $folder 'wfp-filters.xml')"
if ($LASTEXITCODE -ne 0) { throw 'Cannot read Windows Filtering Platform filters.' }
& pktmon list | Set-Content -LiteralPath (Join-Path $folder 'network-components.txt') -Encoding utf8
& pktmon status | Set-Content -LiteralPath (Join-Path $folder 'packet-monitor-status.txt') -Encoding utf8
Write-Host "Diagnostics saved locally: $folder"
# Does not start packet capture or modify filters, firewall, VPN or routes.
# Keep these private network diagnostics out of GitHub.

