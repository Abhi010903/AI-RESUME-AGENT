$ErrorActionPreference = "Continue"
$pgBin = 'C:\Program Files\PostgreSQL\18\bin'
$pgData = 'C:\Users\AbhijitKumar\.postgres18_data'
$pgLog = 'C:\Users\AbhijitKumar\.postgres18_data\server.log'

if (-not (Test-Path $pgData)) {
    Write-Output "Initializing PostgreSQL 18 cluster at $pgData..."
    & "$pgBin\initdb.exe" -D "$pgData" -U resume_agent -A trust -E UTF8
} else {
    Write-Output "PostgreSQL cluster directory exists at $pgData"
}

Write-Output "Checking status or starting PostgreSQL 18 server on port 5432..."
& "$pgBin\pg_ctl.exe" -D "$pgData" status
if ($LASTEXITCODE -ne 0) {
    Write-Output "Starting PostgreSQL server..."
    & "$pgBin\pg_ctl.exe" -D "$pgData" -l "$pgLog" -o "-p 5432" start
    Start-Sleep -Seconds 3
}

Write-Output "Ensuring database resume_agent exists..."
$dbExists = & "$pgBin\psql.exe" -U resume_agent -p 5432 -h 127.0.0.1 -d postgres -t -c "SELECT 1 FROM pg_database WHERE datname = 'resume_agent'"
if (-not $dbExists -or $dbExists.Trim() -ne "1") {
    Write-Output "Creating database resume_agent..."
    & "$pgBin\psql.exe" -U resume_agent -p 5432 -h 127.0.0.1 -d postgres -c "CREATE DATABASE resume_agent OWNER resume_agent;"
} else {
    Write-Output "Database resume_agent already exists."
}

& "$pgBin\psql.exe" -U resume_agent -p 5432 -h 127.0.0.1 -d postgres -c "ALTER USER resume_agent WITH PASSWORD 'resume_agent_secret';"
Write-Output "Verifying connection to resume_agent..."
& "$pgBin\psql.exe" -U resume_agent -p 5432 -h 127.0.0.1 -d resume_agent -c "SELECT current_database(), current_user, version();"
Write-Output "PostgreSQL 18 setup completed successfully."
