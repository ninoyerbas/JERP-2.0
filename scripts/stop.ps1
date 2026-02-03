# Stop JERP 2.0 Application
# PowerShell script to stop the application

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  JERP 2.0 - Stopping Application" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Stopping containers..." -ForegroundColor Yellow
docker-compose down

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ Application stopped successfully!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "✗ Failed to stop application!" -ForegroundColor Red
    exit 1
}
