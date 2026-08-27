# Run in an elevated PowerShell (Right-click → Run as administrator)
# Fixes Expo Go "request timed out" when Node.js inbound is Blocked.

Write-Host "Allowing Node.js inbound + ports 8000/8001..."

Get-NetFirewallRule -DisplayName "Node.js JavaScript Runtime" -ErrorAction SilentlyContinue | ForEach-Object {
  Set-NetFirewallRule -Name $_.Name -Action Allow -Enabled True
  Write-Host "  Node rule $($_.Name) -> Allow"
}

foreach ($item in @(
  @{ Name = "Expo Metro 8001"; Port = 8001 },
  @{ Name = "Expo Metro 8002"; Port = 8002 },
  @{ Name = "Disease Monitoring API 8000"; Port = 8000 }
)) {
  $existing = Get-NetFirewallRule -DisplayName $item.Name -ErrorAction SilentlyContinue
  if (-not $existing) {
    New-NetFirewallRule -DisplayName $item.Name -Direction Inbound -Protocol TCP -LocalPort $item.Port -Action Allow -Profile Any | Out-Null
    Write-Host "  Created $($item.Name)"
  } else {
    Set-NetFirewallRule -DisplayName $item.Name -Action Allow -Enabled True
    Write-Host "  Updated $($item.Name)"
  }
}

Write-Host "Done. Restart Expo (npm start) and retry Expo Go."
