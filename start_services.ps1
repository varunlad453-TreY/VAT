# VAT Enterprise Platform - Service Launcher Script (PowerShell)
# Starts Docker (PostgreSQL pgvector, Redis, FastAPI Backend) + Local Next.js NOC Console

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " VAT ENTERPRISE PLATFORM // NOC SERVICE ORCHESTRATOR" -ForegroundColor Green
Write-Host " Clean Architecture • pgvector HNSW • WebSockets • Next.js NOC" -ForegroundColor DarkCyan
Write-Host "=================================================================" -ForegroundColor Cyan

$WorkspaceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $WorkspaceRoot

# 1. Start Docker Infrastructure (Postgres pgvector, Redis, Backend)
Write-Host "`n[1/3] Starting Docker services (postgres, redis, backend)..." -ForegroundColor Yellow
docker-compose up -d postgres redis backend

if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Docker Compose failed to start services. Please check Docker Desktop." -ForegroundColor Red
    Exit 1
}

Write-Host "[✓] Docker containers started successfully:" -ForegroundColor Green
docker ps --filter "name=vat-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 2. Wait for Backend Health
Write-Host "`n[2/3] Probing FastAPI backend connectivity (http://localhost:8000/health)..." -ForegroundColor Yellow
$MaxRetries = 10
$RetryCount = 0
$BackendReady = $false

while (-not $BackendReady -and $RetryCount -lt $MaxRetries) {
    Start-Sleep -Seconds 1
    $RetryCount++
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.status -eq "healthy" -or $response.status -eq "degraded") {
            $BackendReady = $true
            Write-Host "[✓] Backend is ONLINE! Status: $($response.status) (DB: $($response.database_connected))" -ForegroundColor Green
        }
    } catch {
        Write-Host "    Waiting for backend startup ($RetryCount/$MaxRetries)..." -ForegroundColor DarkGray
    }
}

# 3. Check and Run Frontend NOC Console
Write-Host "`n[3/3] Launching Modern NOC Frontend Console..." -ForegroundColor Yellow
Set-Location "$WorkspaceRoot\frontend"

if (-not (Test-Path "node_modules")) {
    Write-Host "    Installing frontend npm dependencies..." -ForegroundColor Cyan
    npm install
}

Write-Host "`n=================================================================" -ForegroundColor Cyan
Write-Host " NOC CONSOLE READY:" -ForegroundColor Green
Write-Host " • Frontend UI:       http://localhost:3000" -ForegroundColor White
Write-Host " • Backend REST Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host " • Health Endpoint:   http://localhost:8000/health" -ForegroundColor White
Write-Host " • WebSocket Stream:  ws://localhost:8000/ws/telemetry" -ForegroundColor White
Write-Host "=================================================================`n" -ForegroundColor Cyan

npm run dev
