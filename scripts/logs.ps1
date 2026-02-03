# View JERP 2.0 Application Logs
# PowerShell script to view logs

param(
    [string]$Service = "",
    [switch]$Follow = $false
)

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  JERP 2.0 - Application Logs" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Build docker-compose logs command
$logCommand = "docker-compose logs"

if ($Follow) {
    $logCommand += " -f"
}

if ($Service) {
    $logCommand += " $Service"
    Write-Host "Showing logs for: $Service" -ForegroundColor Yellow
} else {
    Write-Host "Showing logs for all services" -ForegroundColor Yellow
    Write-Host "Available services: mysql, redis, backend" -ForegroundColor Gray
    Write-Host "To view specific service: .\scripts\logs.ps1 -Service backend" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Press Ctrl+C to exit" -ForegroundColor Gray
Write-Host ""

# Execute the command
Invoke-Expression $logCommand
