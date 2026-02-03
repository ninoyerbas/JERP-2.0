# JERP 2.0 - Administrator Guide

## Overview

This guide covers administrative tasks for JERP 2.0, including user management, role configuration, system monitoring, and maintenance.

## Initial Setup

### First-Time Login

After installation, use the default superuser account:

- **Email**: `admin@jerp.local`
- **Password**: `Admin123!ChangeMe`

**⚠️ CRITICAL**: Change this password immediately after first login!

### Change Default Password

#### Via API

```powershell
# Login to get token
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"email":"admin@jerp.local","password":"Admin123!ChangeMe"}'

$token = $response.access_token

# Change password
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/change-password" `
  -Method POST `
  -Headers @{
    "Authorization"="Bearer $token"
    "Content-Type"="application/json"
  } `
  -Body '{"old_password":"Admin123!ChangeMe","new_password":"YourNewSecurePassword123!"}'
```

## User Management

### Create New User

```powershell
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

$newUser = @{
    email = "employee@company.com"
    password = "TempPassword123!"
    full_name = "John Doe"
    is_active = $true
    role_id = 4  # Employee role
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users" `
  -Method POST `
  -Headers $headers `
  -Body $newUser
```

### List All Users

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users?skip=0&limit=100" `
  -Method GET `
  -Headers $headers
```

### Deactivate User

```powershell
$userId = 5

$update = @{
    is_active = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/$userId" `
  -Method PUT `
  -Headers $headers `
  -Body $update
```

### Delete User

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/$userId" `
  -Method DELETE `
  -Headers $headers
```

## Role Management

### Default Roles

JERP 2.0 comes with five default roles:

1. **Super Administrator** - Full system access
2. **Administrator** - Administrative access
3. **Manager** - Management access  
4. **Employee** - Standard employee access
5. **Guest** - Read-only access

### View All Roles

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/roles" `
  -Method GET `
  -Headers $headers
```

### Create Custom Role

```powershell
$newRole = @{
    name = "Department Manager"
    description = "Manager with department-specific access"
    is_active = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/roles" `
  -Method POST `
  -Headers $headers `
  -Body $newRole
```

### Assign Role to User

```powershell
$userId = 5
$roleId = 3  # Manager role

$update = @{
    role_id = $roleId
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/$userId" `
  -Method PUT `
  -Headers $headers `
  -Body $update
```

## Permission Management

### View All Permissions

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/roles/permissions/list" `
  -Method GET `
  -Headers $headers
```

### Default Permission Modules

- `users` - User management
- `roles` - Role and permission management
- `audit` - Audit log access
- `compliance` - Compliance management
- `hr` - Human resources
- `payroll` - Payroll management
- `finance` - Financial management

Each module has four actions: `create`, `read`, `update`, `delete`

### Create Custom Permission

```powershell
$newPermission = @{
    code = "inventory.read"
    name = "Read Inventory"
    description = "Permission to view inventory"
    module = "inventory"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/roles/permissions" `
  -Method POST `
  -Headers $headers `
  -Body $newPermission
```

## System Monitoring

### Check System Health

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET
```

Response:
```json
{
  "status": "healthy",
  "app": "JERP 2.0",
  "version": "2.0.0",
  "environment": "production",
  "timestamp": "2024-02-03T10:30:00.000000",
  "checks": {
    "database": "healthy"
  }
}
```

### View Application Logs

```powershell
# View backend logs
docker-compose logs -f backend

# View last 100 lines
docker-compose logs --tail=100 backend

# View MySQL logs
docker-compose logs mysql
```

### View Audit Logs

```powershell
# Get recent audit logs
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/audit/logs?limit=50" `
  -Method GET `
  -Headers $headers

# Filter by action
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/audit/logs?action=login" `
  -Method GET `
  -Headers $headers
```

### Verify Audit Log Integrity

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/audit/verify" `
  -Method GET `
  -Headers $headers
```

## Database Management

### Backup Database

```powershell
# Create backup
docker-compose exec mysql mysqldump -u root -p jerp > backup_$(Get-Date -Format "yyyyMMdd_HHmmss").sql

# Or with environment variable
$env:MYSQL_PWD="your_root_password"
docker-compose exec mysql mysqldump -u root jerp > backup.sql
```

### Restore Database

```powershell
# Stop backend
docker-compose stop backend

# Restore from backup
Get-Content backup.sql | docker-compose exec -T mysql mysql -u root -p jerp

# Start backend
docker-compose start backend
```

### Run Database Migrations

```powershell
# Check current migration version
docker-compose exec backend alembic current

# View migration history
docker-compose exec backend alembic history

# Upgrade to latest
docker-compose exec backend alembic upgrade head

# Downgrade one version
docker-compose exec backend alembic downgrade -1
```

## Maintenance Tasks

### Update JERP 2.0

```powershell
# Backup database first!
# Then update:

# Stop services
docker-compose down

# Pull latest code (if using Git)
git pull

# Rebuild images
docker-compose build

# Start services (migrations run automatically)
docker-compose up -d

# Verify
docker-compose logs -f backend
```

### Restart Services

```powershell
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Clear Cache (Redis)

```powershell
docker-compose exec redis redis-cli FLUSHALL
```

### View Service Status

```powershell
docker-compose ps
```

### View Resource Usage

```powershell
docker stats
```

## Security Best Practices

### 1. Password Policy

- Minimum 12 characters
- Mix of uppercase, lowercase, numbers, and symbols
- Change passwords every 90 days
- No password reuse for last 5 passwords

### 2. Regular Backups

```powershell
# Schedule daily backups (Windows Task Scheduler)
# Create a PowerShell script: backup.ps1

$backupDir = "C:\JERP_Backups"
$date = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "$backupDir\jerp_backup_$date.sql"

# Create directory if it doesn't exist
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir
}

# Backup database
docker-compose exec -T mysql mysqldump -u root -pYourRootPassword jerp > $backupFile

# Keep only last 30 days of backups
Get-ChildItem $backupDir -Filter "*.sql" | 
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
    Remove-Item
```

### 3. Monitor Audit Logs

Review audit logs regularly for suspicious activity:

```powershell
# Check failed login attempts
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/audit/logs?action=login_failed" `
  -Method GET `
  -Headers $headers
```

### 4. Update Environment Variables

After installation, update `.env` with production values:

```env
APP_ENV=production
APP_DEBUG=false
JWT_SECRET_KEY=<long-random-string>
MYSQL_ROOT_PASSWORD=<strong-password>
MYSQL_PASSWORD=<strong-password>
```

### 5. Enable HTTPS

For production, configure HTTPS/TLS:

1. Obtain SSL certificate
2. Update docker-compose to use nginx proxy
3. Configure certificate in nginx
4. Update CORS_ORIGINS in .env

## Troubleshooting

### Backend Won't Start

```powershell
# Check logs
docker-compose logs backend

# Common issues:
# - Database not ready: Wait and retry
# - Migration failed: Check migration logs
# - Port in use: Change port in docker-compose.yml
```

### Database Connection Failed

```powershell
# Verify MySQL is running
docker-compose ps mysql

# Check MySQL logs
docker-compose logs mysql

# Test connection
docker-compose exec mysql mysql -u jerp_user -p jerp
```

### Slow Performance

```powershell
# Check resource usage
docker stats

# Check MySQL slow queries
docker-compose exec mysql mysql -u root -p -e "SHOW PROCESSLIST;"

# Restart services
docker-compose restart
```

### Disk Space Full

```powershell
# Check Docker disk usage
docker system df

# Clean up unused images and volumes
docker system prune -a --volumes

# Keep only recent backups
# Remove old log files
```

## Compliance Management

### View Compliance Dashboard

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/compliance/dashboard?days_back=30" `
  -Method GET `
  -Headers $headers
```

### Generate Compliance Report

```powershell
$report = @{
    report_type = "monthly"
    start_date = "2024-02-01"
    end_date = "2024-02-29"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/compliance/reports" `
  -Method POST `
  -Headers $headers `
  -Body $report
```

## Support

### Getting Help

- **Documentation**: `/docs` directory
- **API Docs**: http://localhost:8000/api/v1/docs
- **GitHub Issues**: https://github.com/ninoyerbas/JERP-2.0/issues

### Log Locations

- **Backend logs**: `docker-compose logs backend`
- **MySQL logs**: `docker-compose logs mysql`
- **Redis logs**: `docker-compose logs redis`

### Contact Support

For enterprise support, contact your system administrator or JERP support team.

## Appendix

### Useful PowerShell Commands

```powershell
# Get API version
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/"

# Count users
$users = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users?limit=1000" -Headers $headers
$users.total

# Export audit logs to CSV
$logs = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/audit/logs?limit=1000" -Headers $headers
$logs.items | Export-Csv -Path "audit_logs.csv" -NoTypeInformation
```

### Database Schema

View current database schema:

```powershell
docker-compose exec mysql mysql -u jerp_user -p jerp -e "SHOW TABLES;"
docker-compose exec mysql mysql -u jerp_user -p jerp -e "DESCRIBE users;"
```

---

**Last Updated**: February 2024  
**Version**: 2.0.0
