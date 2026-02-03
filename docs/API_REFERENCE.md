# JERP 2.0 - API Reference

## Interactive API Documentation

JERP 2.0 provides comprehensive, interactive API documentation through OpenAPI (Swagger).

### Access Documentation

Once JERP 2.0 is running, access the API documentation at:

- **Swagger UI (Interactive)**: http://localhost:8000/api/v1/docs
- **ReDoc (Alternative)**: http://localhost:8000/api/v1/redoc  
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

### Authentication

Most API endpoints require authentication using JWT tokens.

#### 1. Login to Get Tokens

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "admin@jerp.local",
  "password": "Admin123!ChangeMe"
}
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

#### 2. Use Access Token

Include the access token in the `Authorization` header:

```bash
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

## API Endpoints Overview

### Authentication (`/api/v1/auth`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register new user | No |
| POST | `/auth/login` | Login and get tokens | No |
| POST | `/auth/refresh` | Refresh access token | No |
| POST | `/auth/logout` | Logout and create audit log | Yes |
| POST | `/auth/change-password` | Change user password | Yes |
| GET | `/auth/me` | Get current user info | Yes |

### Users (`/api/v1/users`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/users` | List all users (paginated) | Yes |
| POST | `/users` | Create new user | Yes (Superuser) |
| GET | `/users/me` | Get current user | Yes |
| PUT | `/users/me` | Update current user | Yes |
| GET | `/users/{user_id}` | Get user by ID | Yes |
| PUT | `/users/{user_id}` | Update user | Yes |
| DELETE | `/users/{user_id}` | Delete user | Yes (Superuser) |

### Roles & Permissions (`/api/v1/roles`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/roles` | List all roles | Yes |
| POST | `/roles` | Create new role | Yes (Superuser) |
| GET | `/roles/{role_id}` | Get role by ID | Yes |
| PUT | `/roles/{role_id}` | Update role | Yes |
| DELETE | `/roles/{role_id}` | Delete role | Yes (Superuser) |
| GET | `/roles/permissions/list` | List all permissions | Yes |
| POST | `/roles/permissions` | Create permission | Yes (Superuser) |

### Audit Logs (`/api/v1/audit`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/audit/logs` | List audit logs (filtered) | Yes |
| GET | `/audit/logs/{log_id}` | Get audit log by ID | Yes |
| GET | `/audit/verify` | Verify hash chain integrity | Yes |
| GET | `/audit/stats` | Get audit statistics | Yes |

### Compliance (`/api/v1/compliance`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/compliance/violations` | List violations | Yes |
| POST | `/compliance/violations` | Create violation | Yes |
| GET | `/compliance/violations/{id}` | Get violation details | Yes |
| PUT | `/compliance/violations/{id}` | Update violation | Yes |
| DELETE | `/compliance/violations/{id}` | Delete violation | Yes (Superuser) |
| GET | `/compliance/dashboard` | Get compliance dashboard | Yes |
| POST | `/compliance/reports` | Generate compliance report | Yes |

## Common Request Examples

### PowerShell Examples

#### Login
```powershell
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"email":"admin@jerp.local","password":"Admin123!ChangeMe"}'

$token = $response.access_token
```

#### Get Current User
```powershell
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/me" `
  -Method GET `
  -Headers $headers
```

#### List Users
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users?skip=0&limit=10" `
  -Method GET `
  -Headers $headers
```

#### Create Compliance Violation
```powershell
$body = @{
    violation_type = "LABOR_LAW"
    severity = "HIGH"
    standard = "California Labor Code Section 512"
    resource_type = "timesheet"
    resource_id = "123"
    description = "Meal break not provided for 6-hour shift"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/compliance/violations" `
  -Method POST `
  -Headers $headers `
  -Body $body
```

### cURL Examples (Linux/Mac/Git Bash)

#### Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@jerp.local",
    "password": "Admin123!ChangeMe"
  }'
```

#### Get Current User
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

#### List Users
```bash
curl -X GET "http://localhost:8000/api/v1/users?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Response Formats

### Success Response
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-02-03T10:30:00"
}
```

### Error Response
```json
{
  "detail": "Error message describing what went wrong"
}
```

### Paginated Response
```json
{
  "items": [...],
  "total": 100,
  "skip": 0,
  "limit": 10
}
```

## Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |

## Rate Limiting

Currently, JERP 2.0 does not implement rate limiting in Phase 1. Rate limiting will be added in future phases.

## Pagination

Most list endpoints support pagination with query parameters:

- `skip` (default: 0) - Number of records to skip
- `limit` (default: 100, max: 100) - Number of records to return

Example:
```
GET /api/v1/users?skip=20&limit=10
```

## Filtering

Many endpoints support filtering via query parameters. See the interactive documentation for specific filter options for each endpoint.

## Security

- All passwords are hashed using bcrypt
- JWT tokens expire after 30 minutes (access) or 7 days (refresh)
- Audit logs use SHA-256 hash chains for tamper detection
- All API endpoints use HTTPS in production (TLS/SSL)

## Support

For detailed, interactive documentation with request/response examples and the ability to try endpoints directly from your browser, visit:

**http://localhost:8000/api/v1/docs**

For issues or questions:
- GitHub Issues: https://github.com/ninoyerbas/JERP-2.0/issues
- Documentation: See `/docs` directory
