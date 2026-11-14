[CmdletBinding()]
param(
    [ValidatePattern('^\d{1,3}(\.\d{1,3}){3}$')]
    [string]$ListenAddress = '192.168.1.7',
    [ValidatePattern('^\d{1,3}(\.\d{1,3}){3}$')]
    [string]$WslAddress = '172.22.191.85'
)
$ErrorActionPreference = 'Stop'
$principal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run this script from PowerShell as Administrator.'
}
[void][Net.IPAddress]::Parse($ListenAddress)
[void][Net.IPAddress]::Parse($WslAddress)
$local = Get-NetIPAddress -AddressFamily IPv4 -IPAddress $ListenAddress -ErrorAction Stop
if (-not $local) { throw 'Expected LAN address is not assigned. Recheck DHCP.' }
if ($WslAddress -notmatch '^172\.(1[6-9]|2\d|3[01])\.') { throw 'Unexpected WSL private address.' }
$backupDir = Join-Path $env:ProgramData ('Sportfond\network-backups\' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
[void](New-Item -ItemType Directory -Path $backupDir -Force)
$proxyState = & netsh interface portproxy show v4tov4
$proxyState | Set-Content -LiteralPath (Join-Path $backupDir 'portproxy-before.txt') -Encoding utf8
$rules = @(Get-NetFirewallRule -DisplayName 'Sportfond API TCP 80 443' -ErrorAction SilentlyContinue)
if ($rules.Count) { throw 'A Sportfond firewall rule already exists. Inspect before replacing.' }
$regPath = 'HKLM:\SYSTEM\CurrentControlSet\Services\PortProxy\v4tov4\tcp'
foreach ($port in @(80,443)) {
    if (Test-Path $regPath) {
        $existing = Get-ItemPropertyValue -Path $regPath -Name "$ListenAddress/$port" -ErrorAction SilentlyContinue
        if ($existing) { throw "Portproxy $ListenAddress/$port already exists. Inspect first." }
    }
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue |
        Where-Object LocalAddress -in @($ListenAddress,'0.0.0.0','::'))
    if ($listeners.Count) { throw "Port $port is already in use on the LAN address." }
}
Get-Service iphlpsvc | Start-Service
New-NetFirewallRule -DisplayName 'Sportfond API TCP 80 443' -Direction Inbound -Action Allow `
    -Protocol TCP -LocalAddress $ListenAddress -LocalPort 80,443 -InterfaceAlias $local.InterfaceAlias `
    -Profile Any | Out-Null
try {
    foreach ($port in @(80,443)) {
        & netsh interface portproxy add v4tov4 "listenaddress=$ListenAddress" "listenport=$port" "connectaddress=$WslAddress" "connectport=$port"
        if ($LASTEXITCODE -ne 0) { throw "Cannot configure port $port." }
    }
} catch {
    foreach ($port in @(80,443)) {
        & netsh interface portproxy delete v4tov4 "listenaddress=$ListenAddress" "listenport=$port" | Out-Null
    }
    Remove-NetFirewallRule -DisplayName 'Sportfond API TCP 80 443' -ErrorAction SilentlyContinue
    throw
}
Write-Host 'Configured only LAN TCP ports 80 and 443. VPN, Tailscale and other port mappings were not changed.'
Write-Host "Backup: $backupDir"
& netsh interface portproxy show v4tov4
