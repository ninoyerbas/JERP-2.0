# Start JERP 2.0 Application
# PowerShell script to start the application on Windows

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  JERP 2.0 - Starting Application" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker Desktop is running
Write-Host "Checking Docker Desktop..." -ForegroundColor Yellow
try {
    $dockerRunning = docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Docker Desktop is not running!" -ForegroundColor Red
        Write-Host "  Please start Docker Desktop and try again." -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Docker Desktop is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not installed or not accessible!" -ForegroundColor Red
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠ .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✓ .env file created. Please review and update settings." -ForegroundColor Green
        Write-Host ""
        Write-Host "Important: Update the following in .env:" -ForegroundColor Yellow
        Write-Host "  - MYSQL_PASSWORD" -ForegroundColor Yellow
        Write-Host "  - JWT_SECRET_KEY" -ForegroundColor Yellow
        Write-Host "  - INITIAL_SUPERUSER_PASSWORD" -ForegroundColor Yellow
        Write-Host ""
        $continue = Read-Host "Continue with default values? (y/N)"
        if ($continue -ne "y") {
            Write-Host "Exiting. Please update .env and run this script again." -ForegroundColor Yellow
            exit 0
        }
    } else {
        Write-Host "✗ .env.example file not found!" -ForegroundColor Red
        exit 1
    }
}

# Build and start containers
Write-Host ""
Write-Host "Building and starting containers..." -ForegroundColor Yellow
docker-compose up -d --build

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ Application started successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Services:" -ForegroundColor Cyan
    Write-Host "  - Backend API:       http://localhost:8000" -ForegroundColor White
    Write-Host "  - API Docs:          http://localhost:8000/api/v1/docs" -ForegroundColor White
    Write-Host "  - MySQL:             localhost:3306" -ForegroundColor White
    Write-Host "  - Redis:             localhost:6379" -ForegroundColor White
    Write-Host ""
    Write-Host "Default Admin Credentials:" -ForegroundColor Cyan
    Write-Host "  - Email:    admin@jerp.local" -ForegroundColor White
    Write-Host "  - Password: admin123" -ForegroundColor White
    Write-Host ""
    Write-Host "To view logs, run:" -ForegroundColor Yellow
    Write-Host "  .\scripts\logs.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "To stop the application, run:" -ForegroundColor Yellow
    Write-Host "  .\scripts\stop.ps1" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "✗ Failed to start application!" -ForegroundColor Red
    Write-Host "Check the logs with: docker-compose logs" -ForegroundColor Yellow
    exit 1
}
