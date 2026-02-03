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

| Area | Standards |
|------|-----------|
| **Labor Law** | California Labor Code, Federal FLSA |
| **Financial** | GAAP (US), IFRS (International) |
| **Audit** | Immutable SHA-256 hash-chained logs |

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

```bash
# Clone the repository
git clone https://github.com/ninoyerbas/JERP-2.0.git
cd JERP-2.0

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Deploy
docker-compose up -d
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