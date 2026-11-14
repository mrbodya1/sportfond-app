param([string]$PhoneAddress='192.168.1.17',[switch]$Wan)
$ErrorActionPreference='Stop'
$p=[Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if(-not $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Run as Administrator.'}
if($PhoneAddress -notmatch '^192\.168\.1\.\d{1,3}$'){throw 'Unexpected phone address.'}
[void][Net.IPAddress]::Parse($PhoneAddress)
if(@(Get-EtwTraceSession -Name 'PktMon' -ErrorAction SilentlyContinue).Count){throw 'Existing Packet Monitor session: not changed.'}
$before=(& pktmon filter list 2>&1 | Out-String)
if($LASTEXITCODE -ne 0){throw $before}
if($before -match '[\u2568\u2564]'){
 $before=[Text.Encoding]::UTF8.GetString([Text.Encoding]::GetEncoding(866).GetBytes($before))
}
if($before -match '(?im)^\s*\u041d\u0435\u0442\s*$'){$before='No filters'}
if($before -notmatch '(?i)no filters|\u043d\u0435\u0442 \u0444\u0438\u043b\u044c\u0442\u0440|\u043d\u0435 \u043d\u0430\u0441\u0442\u0440\u043e\u0435\u043d|\u043d\u0435 \u0437\u0430\u0434\u0430\u043d|\u043d\u0435 \u0443\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d|\u043e\u0442\u0441\u0443\u0442\u0441\u0442\u0432'){
 Write-Host $before
 throw 'Existing or unfamiliar filter configuration. No changes made.'
}
$dir=Join-Path $env:ProgramData ('Sportfond\network-diagnostics\capture-'+(Get-Date -Format yyyyMMdd-HHmmss))
[void](New-Item -ItemType Directory -Path $dir)
$started=$false
$added=$false
try{
 if($Wan){
  & pktmon filter add SportfondPhoneSyn -d IPv4 -i 192.168.1.7 -t TCP SYN -p 80
 }else{
  & pktmon filter add SportfondPhoneSyn -d IPv4 -i $PhoneAddress 192.168.1.7 -t TCP SYN -p 80
 }
 if($LASTEXITCODE -ne 0){throw 'Filter creation failed.'}
 $added=$true
 & pktmon start --capture --pkt-size 54 --file-size 8 --file-name (Join-Path $dir 'phone.etl')
 if($LASTEXITCODE -ne 0){throw 'Capture start failed.'}
 $started=$true
 if($Wan){
  $controlClient=New-Object Net.Sockets.TcpClient
  try{
   $connectTask=$controlClient.ConnectAsync('192.168.1.1',80)
   if(-not $connectTask.Wait(3000)){throw 'Control connection timed out.'}
   Write-Host 'Control TCP connection to home router established.'
  }finally{$controlClient.Dispose()}
 }
 if($Wan){
  Write-Host 'NOW disable Wi-Fi on the phone and open http://94.50.96.146/sportfond-connectivity using mobile data. Capturing for 30 seconds.'
 }else{
  Write-Host 'NOW open http://192.168.1.7/sportfond-connectivity on the phone using home Wi-Fi. Capturing for 30 seconds.'
 }
 Start-Sleep -Seconds 30
 & pktmon counters --json | Set-Content (Join-Path $dir 'counters.json') -Encoding utf8
}finally{
 if($started){& pktmon stop}
 if($added){
  $current=(& pktmon filter list 2>&1 | Out-String)
  $rows=@($current -split '\r?\n' | Where-Object {$_ -match '^\s*\d+\s+'})
  if($rows.Count -eq 1 -and $rows[0] -match 'SportfondPhoneSyn'){
   & pktmon filter remove
  }else{Write-Warning 'Filter cleanup requires inspection. No existing filters were removed.'}
 }
}
if($started){
 & pktmon etl2txt (Join-Path $dir 'phone.etl') --out (Join-Path $dir 'phone.txt') --brief
 Write-Host "Diagnostics saved locally: $dir"
}
# Captures only TCP SYN headers between the phone and server on port 80.
# No HTTP content. No firewall, VPN or routes are changed. Keep output private.

