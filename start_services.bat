@echo off
title VAT Enterprise Platform - Full Stack Launcher
color 0B

echo =================================================================
echo  VAT ENTERPRISE PLATFORM // NOC SERVICE ORCHESTRATOR
echo  Clean Architecture * pgvector HNSW * WebSockets * Next.js NOC
echo =================================================================

cd /d "%~dp0"

echo.
echo [1/3] Starting Docker services (postgres, redis, backend)...
docker-compose up -d postgres redis backend
if %errorlevel% neq 0 (
    echo [!] Docker Compose failed to start. Ensure Docker Desktop is running.
    pause
    exit /b %errorlevel%
)

echo.
echo [✓] Docker containers active:
docker ps --filter "name=vat-"

echo.
echo [2/3] Checking Frontend dependencies...
cd /d "%~dp0frontend"
if not exist "node_modules\" (
    echo Installing frontend packages...
    call npm install
)

echo.
echo =================================================================
echo  NOC CONSOLE READY:
echo  - Frontend UI:       http://localhost:3000
echo  - Backend REST Docs: http://localhost:8000/docs
echo  - Health Probe:      http://localhost:8000/health
echo  - Live WebSockets:   ws://localhost:8000/ws/telemetry
echo =================================================================
echo.

call npm run dev
pause
