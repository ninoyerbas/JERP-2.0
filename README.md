# JERP 2.0 - On-Premise Compliance ERP Suite

**Julio's Enterprise Resource Planning System - Version 2.0**

A comprehensive, on-premise ERP solution focused on **Labor Law Compliance** and **Financial Compliance (GAAP/IFRS**).

## 🎯 Overview

JERP 2.0 is a complete enterprise resource planning system designed for single-tenant, on-premise deployment. Built from the ground up with compliance as the core focus.

### Target Hardware
- **ACEMAGIC AM08Pro Mini PC**
- AMD Ryzen 9 6900HX (8 cores/16 threads)
- 32GB DDR5 RAM
- 1TB NVMe SSD

## 🔒 Compliance Focus

JERP 2.0 includes a comprehensive compliance framework that automatically monitors and enforces labor laws and financial regulations.

| Area | Standards | Features |
|------|-----------|----------|
| **Labor Law** | California Labor Code, Federal FLSA | Overtime calculations, meal/rest breaks, minimum wage, child labor |
| **Financial** | GAAP (US), IFRS (International) | Revenue recognition, balance sheet validation, inventory methods |
| **Audit** | Immutable SHA-256 hash-chained logs | Tamper-proof audit trail for all compliance violations |

### ✨ Compliance Features

- **Automatic Violation Detection**: Real-time monitoring of timesheets and transactions
- **California Labor Code**: 
  - Daily overtime (1.5x > 8hrs, 2x > 12hrs)
  - 7th day overtime (1.5x first 8hrs, 2x after)
  - Meal and rest break enforcement
  - Minimum wage validation
- **Federal FLSA**:
  - Weekly overtime (1.5x > 40hrs)
  - Employee classification (exempt/non-exempt)
  - Child labor protections
  - Record keeping requirements
- **GAAP Validation**:
  - Balance sheet reconciliation
  - Revenue recognition
  - Inventory valuation (FIFO, LIFO, Average Cost)
  - Depreciation methods
- **IFRS Validation**:
  - IAS 1: Financial statement presentation
  - IAS 2: Inventory (no LIFO)
  - IAS 16: Property, Plant & Equipment
  - Component depreciation
- **Violation Tracking**: Full lifecycle management with assignment and resolution
- **Compliance Reports**: Automated reporting and analytics
- **Dashboard**: Real-time compliance score and violation trends

## 📦 Modules

- Core (Auth, RBAC, Security)
- HR/HRIS
- Payroll (with compliance enforcement)
- CRM
- Finance (GAAP/IFRS validated)
- Inventory
- Procurement
- Manufacturing
- Project Management
- Helpdesk
- BI/Reports
- Notifications
- Documents
- Workflow Engine
- AI/ML
- Multi-language (i18n)
- Mobile Support

## 🚀 Quick Start

### Windows 11 (Recommended - Using Docker)

```powershell
# Clone the repository
git clone https://github.com/ninoyerbas/JERP-2.0.git
cd JERP-2.0

# Configure environment
Copy-Item .env.example .env
# Edit .env with your settings (use notepad or your preferred editor)

# Start with Docker Compose (requires Docker Desktop)
.\scripts\start-windows.ps1

# Or manually:
docker-compose up -d
```

**Default Superuser:**
- Email: `admin@jerp.local`
- Password: `Admin123!ChangeMe` (⚠️ Change after first login!)

Access the application:
- API: `http://localhost:8000`
- API Docs: `http://localhost:8000/api/v1/docs`
- Health Check: `http://localhost:8000/health`

See [Installation Guide](docs/INSTALLATION.md) for detailed Windows setup.

### Linux/Mac (Local Development)

```bash
git clone https://github.com/ninoyerbas/JERP-2.0.git
cd JERP-2.0
cp .env.example .env
# Edit .env with your settings (see below)
```

**Important:** Update these values in `.env`:
```env
MYSQL_ROOT_PASSWORD=your_secure_root_password
MYSQL_PASSWORD=your_secure_password
JWT_SECRET_KEY=your_very_long_random_secret_key_at_least_32_chars
INITIAL_SUPERUSER_EMAIL=admin@jerp.local
INITIAL_SUPERUSER_PASSWORD=admin123  # Change in production!
```

#### 2. Start with Docker Compose

**Option A: Using PowerShell Scripts (Windows - Recommended)**
```powershell
# Start all services
.\scripts\start.ps1

# View logs
.\scripts\logs.ps1

# Stop services
.\scripts\stop.ps1

# Reset database (development)
.\scripts\reset.ps1
```

**Option B: Using Docker Compose Directly**
```bash
# Start all services (MySQL, Redis, Backend)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### 3. Verify Installation

```bash
# Check service health
docker-compose ps

# All services should show as "healthy"
# Access API health check
curl http://localhost:8000/health
```

#### 4. Access Application

- **Backend API:** http://localhost:8000
- **API Documentation (Swagger):** http://localhost:8000/api/v1/docs
- **API Documentation (ReDoc):** http://localhost:8000/api/v1/redoc

**Default Admin Credentials:**
- Email: `admin@jerp.local`
- Password: `admin123` (configurable in `.env`)

### Development Setup

For development with hot reload:

```bash
# Start with development configuration
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Code changes in backend/ will automatically reload
```

### Database Management

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create superuser interactively
docker-compose exec backend python manage.py user:create-superuser

# View migration status
docker-compose exec backend python manage.py db:status

# Access MySQL shell
docker-compose exec mysql mysql -u jerp_user -p jerp
```

### Docker Services

The application consists of three services:

| Service | Description | Port | Health Check |
|---------|-------------|------|--------------|
| **mysql** | MySQL 8.0 database | 3306 | `mysqladmin ping` |
| **redis** | Redis 7 cache | 6379 | `redis-cli ping` |
| **backend** | FastAPI application | 8000 | `/health` endpoint |

**Data Persistence:**
- MySQL data: `jerp_mysql_data` volume
- Redis data: `jerp_redis_data` volume

### Manual Installation (Without Docker)

If you prefer to run without Docker:

```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Initialize database
python scripts/init_db.py

# Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access the API documentation at: `http://localhost:8000/api/v1/docs`

## 🔧 API Examples

### Create a Compliance Violation

```bash
curl -X POST http://localhost:8000/api/v1/compliance/violations \
  -H "Content-Type: application/json" \
  -d '{
    "violation_type": "LABOR_LAW",
    "regulation": "California Labor Code Section 512",
    "severity": "HIGH",
    "description": "Meal break not provided for 6-hour shift",
    "entity_type": "timesheet",
    "entity_id": 123
  }'
```

### Get Compliance Dashboard

```bash
curl http://localhost:8000/api/v1/compliance/dashboard?days_back=30
```

### Generate Compliance Report

```bash
curl -X POST http://localhost:8000/api/v1/compliance/reports \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "monthly",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  }'
```

## 📚 Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [Compliance Guide](docs/COMPLIANCE_GUIDE.md)
- [Admin Guide](docs/ADMIN_GUIDE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Statement of Work](SOW.md)

## 🔌 API Endpoints

JERP 2.0 provides a comprehensive RESTful API with OpenAPI documentation.

### Access API Documentation
- **Swagger UI**: `http://localhost:8000/api/v1/docs`
- **ReDoc**: `http://localhost:8000/api/v1/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/v1/openapi.json`

### Authentication Flow

1. **Register a new user**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword",
    "full_name": "John Doe"
  }'
```

2. **Login and get JWT tokens**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword"
  }'
```

3. **Use access token for authenticated requests**:
```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### API Endpoints Overview

#### Authentication (7 endpoints)
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout (creates audit log)
- `POST /api/v1/auth/change-password` - Change password
- `GET /api/v1/auth/me` - Get current user info

#### User Management (7 endpoints)
- `GET /api/v1/users` - List users (paginated)
- `POST /api/v1/users` - Create user (superuser only)
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/me` - Update current user
- `GET /api/v1/users/{user_id}` - Get user by ID
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user (superuser only)

#### Roles & Permissions (7 endpoints)
- `GET /api/v1/roles` - List roles
- `POST /api/v1/roles` - Create role (superuser only)
- `GET /api/v1/roles/{role_id}` - Get role by ID
- `PUT /api/v1/roles/{role_id}` - Update role
- `DELETE /api/v1/roles/{role_id}` - Delete role
- `GET /api/v1/roles/permissions/list` - List permissions
- `POST /api/v1/roles/permissions` - Create permission

#### Audit Logs (4 endpoints)
- `GET /api/v1/audit/logs` - List audit logs (filtered, paginated)
- `GET /api/v1/audit/logs/{log_id}` - Get audit log by ID
- `GET /api/v1/audit/verify` - Verify hash chain integrity
- `GET /api/v1/audit/stats` - Get audit statistics

### Security Features

- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control**: Fine-grained permission system
- **Audit Logging**: Immutable SHA-256 hash-chained audit trail
- **Password Hashing**: Bcrypt password encryption
- **Input Validation**: Pydantic schema validation
- **CORS Protection**: Configurable CORS policies

## 📄 License

MIT License - See LICENSE file for details.

---

**JERP 2.0** - Enterprise Compliance Made Simple