$ErrorActionPreference = "Continue"
$stdout = "C:\Coding\Projects\AI-RESUME-AGENT\user\server.stdout.log"
$stderr = "C:\Coding\Projects\AI-RESUME-AGENT\user\server.stderr.log"

if (Test-Path $stdout) { Remove-Item $stdout }
if (Test-Path $stderr) { Remove-Item $stderr }

Write-Output "Starting server with log redirection..."
$proc = Start-Process -FilePath "pnpm.cmd" -ArgumentList "run", "--filter", "server", "dev" -WorkingDirectory "C:\Coding\Projects\AI-RESUME-AGENT\user" -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru

Start-Sleep -Seconds 10

Write-Output "--- STDOUT ---"
if (Test-Path $stdout) { Get-Content $stdout }
Write-Output "--- STDERR ---"
if (Test-Path $stderr) { Get-Content $stderr }

Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*pnpm*" -or $_.CommandLine -like "*tsx*" } | Stop-Process -Force -ErrorAction SilentlyContinue
