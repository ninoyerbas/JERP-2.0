# Reset JERP 2.0 Database
# PowerShell script to reset the database (DEVELOPMENT ONLY)

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  JERP 2.0 - Reset Database" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "⚠ WARNING: This will delete ALL data in the database!" -ForegroundColor Yellow -BackgroundColor Red
Write-Host ""

$confirm = Read-Host "Are you sure you want to continue? Type 'yes' to confirm"

if ($confirm -ne "yes") {
    Write-Host "Operation cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Stopping containers..." -ForegroundColor Yellow
docker-compose down

Write-Host "Removing database volumes..." -ForegroundColor Yellow
docker volume rm jerp_mysql_data -f 2>&1 | Out-Null
docker volume rm jerp_redis_data -f 2>&1 | Out-Null

Write-Host "Starting containers..." -ForegroundColor Yellow
docker-compose up -d

Write-Host ""
Write-Host "Waiting for database to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "Running database migrations..." -ForegroundColor Yellow
docker-compose exec -T backend alembic upgrade head

Write-Host "Initializing database with default data..." -ForegroundColor Yellow
docker-compose exec -T backend python manage.py db:init

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ Database reset successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Default Admin Credentials:" -ForegroundColor Cyan
    Write-Host "  - Email:    admin@jerp.local" -ForegroundColor White
    Write-Host "  - Password: admin123" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "✗ Database reset failed!" -ForegroundColor Red
    Write-Host "Check logs with: .\scripts\logs.ps1 -Service backend" -ForegroundColor Yellow
    exit 1
}
