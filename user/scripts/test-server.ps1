$ErrorActionPreference = "Continue"
Write-Output "Starting server..."
$proc = Start-Process -FilePath "pnpm.cmd" -ArgumentList "run", "--filter", "server", "dev" -WorkingDirectory "C:\Coding\Projects\AI-RESUME-AGENT\user" -PassThru

$started = $false
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 2
    try {
        $res = Invoke-RestMethod -Uri "http://localhost:3001/api/health" -Method Get -TimeoutSec 3 -ErrorAction Stop
        Write-Output "Health check succeeded!"
        Write-Output ($res | ConvertTo-Json -Depth 4)
        $started = $true
        break
    } catch {
        Write-Output "Waiting for server to become ready ($i)..."
    }
}

if (-not $started) {
    Write-Output "Server failed to respond in time."
}

Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*pnpm*" -or $_.CommandLine -like "*tsx*" } | Stop-Process -Force -ErrorAction SilentlyContinue
