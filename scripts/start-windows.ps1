#!/usr/bin/env pwsh
# JERP 2.0 - Windows Deployment Script

Write-Host "JERP 2.0 - Starting Deployment on Windows 11" -ForegroundColor Green

# Check Docker Desktop
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Docker Desktop not found. Please install Docker Desktop for Windows." -ForegroundColor Red
    exit 1
}

# Check if Docker is running
docker info | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker Desktop is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Create .env if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "Please edit .env with your configuration before continuing." -ForegroundColor Yellow
    exit 0
}

# Start services
Write-Host "Starting JERP 2.0 services..." -ForegroundColor Cyan
docker-compose up -d

# Wait for services
Write-Host "Waiting for services to be healthy..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

# Check service status
docker-compose ps

Write-Host ""
Write-Host "JERP 2.0 is starting!" -ForegroundColor Green
Write-Host "  - API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "  - API Docs: http://localhost:8000/api/v1/docs" -ForegroundColor Cyan
Write-Host "  - Health Check: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "To view logs: docker-compose logs -f backend" -ForegroundColor Yellow
Write-Host "To stop: docker-compose down" -ForegroundColor Yellow
