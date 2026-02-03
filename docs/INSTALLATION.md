# JERP 2.0 - Installation Guide

## Windows 11 Installation

This guide will help you install and set up JERP 2.0 on Windows 11 using Docker Desktop.

## Prerequisites

### Required Software

1. **Windows 11** (64-bit)
2. **Docker Desktop for Windows** (version 4.0 or higher)
3. **PowerShell 5.1 or higher** (included with Windows 11)
4. **Git for Windows** (optional, for cloning the repository)

### Hardware Requirements

**Recommended:**
- AMD Ryzen 9 6900HX or equivalent (8 cores/16 threads)
- 32GB DDR5 RAM
- 1TB NVMe SSD
- 10GB free disk space for Docker images

**Minimum:**
- Dual-core processor with virtualization support
- 8GB RAM
- 20GB free disk space

## Step 1: Install Docker Desktop

1. Download Docker Desktop for Windows from [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)

2. Run the installer and follow the installation wizard

3. Enable WSL 2 backend when prompted (recommended)

4. Restart your computer when installation completes

5. Launch Docker Desktop and wait for it to start

6. Verify Docker is running:
   ```powershell
   docker --version
   docker info
   ```

## Step 2: Clone the Repository

```powershell
# Using Git
git clone https://github.com/ninoyerbas/JERP-2.0.git
cd JERP-2.0

# Or download and extract the ZIP file from GitHub
```

## Step 3: Configure Environment

1. Create your `.env` file from the example:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Edit `.env` with your preferred text editor (Notepad, VSCode, etc.):
   ```powershell
   notepad .env
   ```

3. **IMPORTANT:** Update these security-critical values:
   - `MYSQL_ROOT_PASSWORD` - Strong password for MySQL root user
   - `MYSQL_PASSWORD` - Strong password for application database user
   - `JWT_SECRET_KEY` - Long random string for JWT token signing

   Example secure values:
   ```env
   MYSQL_ROOT_PASSWORD=MyS3cur3R00tP@ssw0rd!2024
   MYSQL_PASSWORD=MyS3cur3AppP@ssw0rd!2024
   JWT_SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
   ```

## Step 4: Start JERP 2.0

### Using PowerShell Script (Recommended)

```powershell
.\scripts\start-windows.ps1
```

The script will:
- Check Docker Desktop is running
- Verify prerequisites
- Start all services (MySQL, Redis, Backend)
- Run database migrations
- Initialize default data
- Display access URLs

### Manual Start (Alternative)

```powershell
docker-compose up -d
```

## Step 5: Verify Installation

1. **Check service status:**
   ```powershell
   docker-compose ps
   ```

   All services should show "Up" status.

2. **View logs:**
   ```powershell
   # All services
   docker-compose logs

   # Backend only
   docker-compose logs -f backend

   # MySQL only
   docker-compose logs -f mysql
   ```

3. **Access the application:**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/api/v1/docs
   - Health Check: http://localhost:8000/health

4. **Test health check:**
   ```powershell
   curl http://localhost:8000/health
   ```

   Or open http://localhost:8000/health in your browser.

## Step 6: First Login

### Default Superuser Account

- **Email:** `admin@jerp.local`
- **Password:** `Admin123!ChangeMe`

**⚠️ CRITICAL:** Change this password immediately after first login!

### Change Password via API

```powershell
# Login to get access token
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"email":"admin@jerp.local","password":"Admin123!ChangeMe"}'

$token = $response.access_token

# Change password
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/change-password" `
  -Method POST `
  -Headers @{
    "Content-Type"="application/json"
    "Authorization"="Bearer $token"
  } `
  -Body '{"old_password":"Admin123!ChangeMe","new_password":"YourNewSecurePassword123!"}'
```

## Managing JERP 2.0

### Stop Services

```powershell
docker-compose down
```

### Restart Services

```powershell
docker-compose restart
```

### Stop and Remove All Data

**⚠️ WARNING:** This will delete all data!

```powershell
docker-compose down -v
```

### View Real-Time Logs

```powershell
docker-compose logs -f backend
```

### Update JERP 2.0

```powershell
# Stop services
docker-compose down

# Pull latest changes (if using Git)
git pull

# Rebuild images
docker-compose build

# Start services
docker-compose up -d
```

## Troubleshooting

### Docker Desktop Not Starting

1. Ensure virtualization is enabled in BIOS
2. Check Windows features: Hyper-V and WSL 2 should be enabled
3. Restart Docker Desktop
4. Check Docker Desktop logs

### Port Already in Use

If ports 3306, 6379, or 8000 are in use:

1. Find what's using the port:
   ```powershell
   netstat -ano | findstr :8000
   ```

2. Either:
   - Stop the conflicting service
   - Or change port in `docker-compose.yml` and `.env`

### Database Connection Errors

1. Check MySQL is running:
   ```powershell
   docker-compose ps mysql
   ```

2. View MySQL logs:
   ```powershell
   docker-compose logs mysql
   ```

3. Verify database credentials in `.env`

### Migration Errors

If migrations fail, you can run them manually:

```powershell
docker-compose exec backend alembic upgrade head
```

### Reset Database

To completely reset the database:

```powershell
# Stop services
docker-compose down

# Remove volumes
docker volume rm jerp-20_mysql_data

# Start fresh
docker-compose up -d
```

## Production Deployment

For production deployment, use the production override:

```powershell
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**Production Checklist:**
- [ ] Change all default passwords
- [ ] Set `APP_ENV=production` in `.env`
- [ ] Set `APP_DEBUG=false` in `.env`
- [ ] Use strong, unique `JWT_SECRET_KEY`
- [ ] Configure firewall rules
- [ ] Set up SSL/TLS certificates
- [ ] Configure backup strategy
- [ ] Set up monitoring and logging
- [ ] Review security settings

## Getting Help

- **Documentation:** See `docs/` directory
- **Issues:** Report at https://github.com/ninoyerbas/JERP-2.0/issues
- **API Docs:** http://localhost:8000/api/v1/docs

## Next Steps

- Read the [Development Guide](DEVELOPMENT.md)
- Review the [Compliance Guide](COMPLIANCE_GUIDE.md)
- Explore the [API Reference](API_REFERENCE.md)
