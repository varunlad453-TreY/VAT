# VAT Enterprise Platform - Service Launcher Script (PowerShell)
# Starts Docker (PostgreSQL pgvector, Redis, FastAPI Backend) + Local Next.js NOC Console

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " VAT ENTERPRISE PLATFORM // NOC SERVICE ORCHESTRATOR" -ForegroundColor Green
Write-Host " Clean Architecture • pgvector HNSW • WebSockets • Next.js NOC" -ForegroundColor DarkCyan
Write-Host "=================================================================" -ForegroundColor Cyan

# 1. Start Docker Infrastructure (Postgres pgvector, Redis, Backend)
Write-Host "`n[1/3] Starting Docker services (postgres, redis, backend)..." -ForegroundColor Yellow
docker-compose up -d postgres redis backend

Write-Host "`n[2/3] Checking Docker container status..." -ForegroundColor Yellow
docker ps --filter "name=vat-"

# 3. Check and Run Frontend NOC Console
Write-Host "`n[3/3] Launching Modern NOC Frontend Console..." -ForegroundColor Yellow
Set-Location "$PSScriptRoot\frontend"

Write-Host "`n=================================================================" -ForegroundColor Cyan
Write-Host " NOC CONSOLE READY:" -ForegroundColor Green
Write-Host " • Frontend UI:       http://localhost:3000" -ForegroundColor White
Write-Host " • Backend REST Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host " • Health Endpoint:   http://localhost:8000/health" -ForegroundColor White
Write-Host " • WebSocket Stream:  ws://localhost:8000/ws/telemetry" -ForegroundColor White
Write-Host "=================================================================`n" -ForegroundColor Cyan

npm run dev
