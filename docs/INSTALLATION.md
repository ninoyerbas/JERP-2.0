# JERP 2.0 - Installation Guide

Complete installation guide for JERP 2.0 on Windows 11.

## Prerequisites

### Required Software

1. **Windows 11**
   - Any edition (Home, Pro, Enterprise)
   - 64-bit version required

2. **Docker Desktop for Windows**
   - Version 4.x or later
   - Download: https://www.docker.com/products/docker-desktop/
   - Requires WSL 2 backend

3. **Git for Windows**
   - Download: https://git-scm.com/download/win
   - Used to clone the repository

### Recommended Software

- **VS Code** - For development: https://code.visualstudio.com/
- **Windows Terminal** - Better terminal experience: https://aka.ms/terminal
- **MySQL Workbench** - Database management (optional): https://dev.mysql.com/downloads/workbench/

## Installation Steps

### 1. Install Docker Desktop

1. Download Docker Desktop from https://www.docker.com/products/docker-desktop/
2. Run the installer and follow the installation wizard
3. Enable WSL 2 when prompted
4. Restart your computer if required
5. Start Docker Desktop and wait for it to be ready
6. Verify installation:
   ```powershell
   docker --version
   docker-compose --version
   ```

### 2. Configure Docker Desktop

1. Open Docker Desktop Settings (System Tray → Docker Icon → Settings)
2. **Resources:**
   - CPUs: Allocate at least 4 cores
   - Memory: Allocate at least 8GB RAM
   - Disk: Ensure at least 20GB available

3. **Docker Engine:**
   - Keep default settings (unless you have specific requirements)

4. Apply & Restart Docker Desktop

### 3. Clone the Repository

Open PowerShell or Windows Terminal:

```powershell
# Clone the repository
git clone https://github.com/ninoyerbas/JERP-2.0.git

# Navigate to the project directory
cd JERP-2.0
```

### 4. Configure Environment Variables

1. Copy the example environment file:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Edit `.env` file with your preferred text editor (Notepad, VS Code, etc.):
   ```powershell
   notepad .env
   # or
   code .env
   ```

3. **Important: Update these values:**
   ```env
   # Change these passwords!
   MYSQL_ROOT_PASSWORD=your_secure_root_password_here
   MYSQL_PASSWORD=your_secure_password_here
   JWT_SECRET_KEY=your_very_long_random_secret_key_at_least_32_characters
   INITIAL_SUPERUSER_PASSWORD=your_admin_password_here
   ```

4. **Optional: Update these values:**
   ```env
   # Initial superuser credentials
   INITIAL_SUPERUSER_EMAIL=your_email@example.com
   INITIAL_SUPERUSER_NAME=Your Name
   
   # Application settings
   APP_ENV=development  # or 'production'
   APP_DEBUG=true       # false for production
   ```

### 5. Start the Application

#### Option A: Using PowerShell Scripts (Recommended)

```powershell
# Start the application
.\scripts\start.ps1
```

This script will:
- Check if Docker Desktop is running
- Create `.env` from `.env.example` if needed
- Build and start all containers
- Display service URLs and credentials

#### Option B: Using Docker Compose Directly

```powershell
# Build and start containers
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop with Ctrl+C
```

### 6. Wait for Services to Initialize

The first startup takes 2-3 minutes as it:
- Downloads Docker images (MySQL, Redis)
- Builds the backend application
- Initializes the database
- Runs migrations
- Seeds initial data

Monitor progress:
```powershell
# View all logs
.\scripts\logs.ps1

# Or view backend logs only
.\scripts\logs.ps1 -Service backend
```

### 7. Verify Installation

1. **Check services are running:**
   ```powershell
   docker-compose ps
   ```
   
   All services should show as "Up" and "healthy":
   - jerp_mysql
   - jerp_redis
   - jerp_backend

2. **Test backend API:**
   - Open browser: http://localhost:8000/health
   - Should return JSON with `"status": "healthy"`

3. **Access API documentation:**
   - Open browser: http://localhost:8000/api/v1/docs
   - Interactive Swagger UI should load

4. **Test login:**
   - Use default credentials (from `.env`):
     - Email: `admin@jerp.local`
     - Password: `admin123` (or your custom password)

## Post-Installation

### Access Services

- **Backend API:** http://localhost:8000
- **API Documentation (Swagger):** http://localhost:8000/api/v1/docs
- **API Documentation (ReDoc):** http://localhost:8000/api/v1/redoc
- **MySQL Database:** localhost:3306
- **Redis Cache:** localhost:6379

### Default Credentials

**Superuser:**
- Email: `admin@jerp.local` (configurable in `.env`)
- Password: `admin123` (configurable in `.env`)

**MySQL Database:**
- Host: `localhost` (or `mysql` from inside containers)
- Port: `3306`
- Database: `jerp`
- User: `jerp_user`
- Password: (from `.env` MYSQL_PASSWORD)

### Common Commands

```powershell
# View logs
.\scripts\logs.ps1

# View specific service logs
.\scripts\logs.ps1 -Service backend

# Stop application
.\scripts\stop.ps1

# Restart application
.\scripts\stop.ps1
.\scripts\start.ps1

# Reset database (WARNING: Deletes all data!)
.\scripts\reset.ps1
```

## Troubleshooting

### Docker Desktop Not Starting

**Issue:** Docker Desktop fails to start or shows "Docker is not running"

**Solutions:**
1. Ensure Windows Subsystem for Linux (WSL 2) is installed:
   ```powershell
   wsl --install
   wsl --set-default-version 2
   ```

2. Enable Hyper-V and Containers features (PowerShell as Administrator):
   ```powershell
   Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
   Enable-WindowsOptionalFeature -Online -FeatureName Containers -All
   ```

3. Restart Windows

### Port Already in Use

**Issue:** Error: "bind: address already in use"

**Solutions:**
1. Check what's using the port:
   ```powershell
   netstat -ano | findstr :8000
   netstat -ano | findstr :3306
   netstat -ano | findstr :6379
   ```

2. Stop the conflicting service or change ports in `.env`:
   ```env
   MYSQL_PORT=3307  # Change from 3306
   REDIS_PORT=6380  # Change from 6379
   ```

### Database Connection Failed

**Issue:** Backend can't connect to MySQL

**Solutions:**
1. Check MySQL is healthy:
   ```powershell
   docker-compose ps mysql
   ```

2. View MySQL logs:
   ```powershell
   .\scripts\logs.ps1 -Service mysql
   ```

3. Restart services:
   ```powershell
   docker-compose restart mysql
   docker-compose restart backend
   ```

### Migration Errors

**Issue:** Alembic migration fails

**Solutions:**
1. Check database is running:
   ```powershell
   docker-compose ps mysql
   ```

2. Run migrations manually:
   ```powershell
   docker-compose exec backend alembic upgrade head
   ```

3. Check migration history:
   ```powershell
   docker-compose exec backend alembic current
   ```

### Permission Denied Errors

**Issue:** Cannot write to files or volumes

**Solutions:**
1. Run PowerShell as Administrator
2. Ensure Docker Desktop has access to the drive:
   - Docker Desktop Settings → Resources → File Sharing
   - Add the project directory

### Container Exits Immediately

**Issue:** Backend container starts then exits

**Solutions:**
1. Check logs for errors:
   ```powershell
   .\scripts\logs.ps1 -Service backend
   ```

2. Common causes:
   - Invalid Python code (syntax errors)
   - Missing dependencies
   - Database not ready

3. Rebuild container:
   ```powershell
   docker-compose build backend --no-cache
   docker-compose up -d backend
   ```

## Uninstallation

To completely remove JERP 2.0:

```powershell
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: Deletes all data!)
docker volume rm jerp_mysql_data
docker volume rm jerp_redis_data

# Remove images
docker images | findstr jerp
docker rmi <image_id>

# Delete project directory
cd ..
Remove-Item -Recurse -Force JERP-2.0
```

## Next Steps

- Read [Development Guide](DEVELOPMENT.md) for development workflow
- Read [Compliance Guide](COMPLIANCE_GUIDE.md) for compliance features
- Explore API at http://localhost:8000/api/v1/docs

## Support

For issues or questions:
- GitHub Issues: https://github.com/ninoyerbas/JERP-2.0/issues
- Documentation: https://github.com/ninoyerbas/JERP-2.0/tree/main/docs
