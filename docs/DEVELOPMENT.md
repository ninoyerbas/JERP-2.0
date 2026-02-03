# JERP 2.0 - Development Guide

Developer guide for working with JERP 2.0.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Database Migrations](#database-migrations)
- [Development Workflow](#development-workflow)
- [Hot Reload](#hot-reload)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Debugging](#debugging)

## Development Setup

### Prerequisites

- Completed [Installation Guide](INSTALLATION.md)
- Docker Desktop running
- Code editor (VS Code recommended)

### Start Development Environment

Use the development override configuration for hot reload and debugging:

```powershell
# Start with development configuration
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Or use regular configuration (no hot reload)
docker-compose up -d
```

### Access Development Tools

- **Backend API:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/api/v1/docs
- **API Docs (ReDoc):** http://localhost:8000/api/v1/redoc
- **MySQL:** localhost:3306
- **Redis:** localhost:6379

## Project Structure

```
JERP-2.0/
├── backend/                    # Backend application
│   ├── alembic/               # Database migrations
│   │   ├── versions/          # Migration files
│   │   ├── env.py            # Alembic environment
│   │   └── script.py.mako    # Migration template
│   ├── app/                   # Application code
│   │   ├── api/              # API endpoints
│   │   │   └── v1/           # API version 1
│   │   │       ├── endpoints/  # Endpoint modules
│   │   │       └── router.py   # API router
│   │   ├── core/             # Core modules
│   │   │   ├── config.py     # Configuration
│   │   │   ├── database.py   # Database connection
│   │   │   ├── security.py   # Security utilities
│   │   │   ├── startup.py    # Startup tasks
│   │   │   └── deps.py       # Dependencies
│   │   ├── models/           # Database models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── scripts/          # Management scripts
│   │   └── main.py           # FastAPI application
│   ├── tests/                # Tests
│   ├── requirements.txt      # Python dependencies
│   ├── alembic.ini          # Alembic configuration
│   └── manage.py            # Management CLI
├── docs/                     # Documentation
├── scripts/                  # PowerShell scripts
├── docker-compose.yml        # Docker Compose config
├── docker-compose.dev.yml    # Development overrides
├── Dockerfile               # Backend Docker image
├── .env.example             # Environment template
└── README.md                # Project overview
```

## Database Migrations

### Overview

JERP 2.0 uses Alembic for database migrations. Migrations track changes to database schema over time.

### Creating Migrations

#### Auto-generate Migration

When you modify models, create a migration:

```powershell
# From project root
docker-compose exec backend alembic revision --autogenerate -m "Add new table"

# Or using manage.py
docker-compose exec backend python manage.py db:migrate -m "Add new table"
```

This generates a new migration file in `backend/alembic/versions/`.

#### Manual Migration

For complex changes, create a blank migration:

```powershell
docker-compose exec backend alembic revision -m "Custom migration"
```

Edit the generated file to add your changes.

### Running Migrations

```powershell
# Upgrade to latest
docker-compose exec backend alembic upgrade head

# Or using manage.py
docker-compose exec backend python manage.py db:upgrade

# Upgrade to specific revision
docker-compose exec backend alembic upgrade <revision_id>
```

### Downgrading Migrations

```powershell
# Downgrade one revision
docker-compose exec backend alembic downgrade -1

# Or using manage.py
docker-compose exec backend python manage.py db:downgrade

# Downgrade to specific revision
docker-compose exec backend alembic downgrade <revision_id>
```

### Viewing Migration Status

```powershell
# Show current revision
docker-compose exec backend alembic current

# Show migration history
docker-compose exec backend alembic history

# Or using manage.py
docker-compose exec backend python manage.py db:status
```

### Migration Best Practices

1. **Always review auto-generated migrations** - Alembic may not detect all changes correctly
2. **Test migrations both ways** - Ensure both upgrade and downgrade work
3. **Add data migrations carefully** - Consider impact on existing data
4. **Keep migrations small** - One logical change per migration
5. **Never edit applied migrations** - Create a new migration instead
6. **Backup database before migrations** - Especially in production

### Example Migration Workflow

```powershell
# 1. Modify a model (e.g., add field to User)
# Edit backend/app/models/user.py

# 2. Generate migration
docker-compose exec backend alembic revision --autogenerate -m "Add user phone field"

# 3. Review the generated migration file
# backend/alembic/versions/YYYY_MM_DD_xxxx_add_user_phone_field.py

# 4. Apply migration
docker-compose exec backend alembic upgrade head

# 5. Verify in database
docker-compose exec mysql mysql -u jerp_user -p jerp -e "DESCRIBE users;"
```

## Development Workflow

### 1. Making Code Changes

The backend code is mounted as a volume for hot reload:

```powershell
# Development mode - changes reload automatically
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

Edit files in `backend/app/` and the server will reload automatically.

### 2. Adding New Dependencies

```powershell
# 1. Add dependency to requirements.txt
# Edit backend/requirements.txt

# 2. Rebuild container
docker-compose build backend

# 3. Restart
docker-compose up -d backend
```

### 3. Adding New Models

```python
# 1. Create model in backend/app/models/
# backend/app/models/my_model.py

from sqlalchemy import Column, Integer, String
from app.core.database import Base

class MyModel(Base):
    __tablename__ = "my_table"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
```

```python
# 2. Import in backend/app/models/__init__.py
from app.models.my_model import MyModel

__all__ = [..., "MyModel"]
```

```powershell
# 3. Generate and apply migration
docker-compose exec backend alembic revision --autogenerate -m "Add MyModel"
docker-compose exec backend alembic upgrade head
```

### 4. Adding New API Endpoints

```python
# 1. Create endpoint in backend/app/api/v1/endpoints/
# backend/app/api/v1/endpoints/my_endpoint.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter()

@router.get("/my-endpoint")
async def my_endpoint(db: Session = Depends(get_db)):
    return {"message": "Hello from my endpoint"}
```

```python
# 2. Include in router (backend/app/api/v1/router.py)
from app.api.v1.endpoints import my_endpoint

api_router.include_router(
    my_endpoint.router,
    prefix="/my-endpoint",
    tags=["my-endpoint"]
)
```

```powershell
# 3. Test endpoint
curl http://localhost:8000/api/v1/my-endpoint
```

## Hot Reload

### Backend Hot Reload

When using `docker-compose.dev.yml`, changes to Python files automatically reload the server:

```powershell
# Start with hot reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Watch logs to see reloads
.\scripts\logs.ps1 -Service backend -Follow
```

### Disable Hot Reload

Use standard `docker-compose.yml` (without dev override):

```powershell
docker-compose up -d
```

## Testing

### Running Tests

```powershell
# Run all tests
docker-compose exec backend pytest

# Run specific test file
docker-compose exec backend pytest tests/test_auth.py

# Run with coverage
docker-compose exec backend pytest --cov=app --cov-report=html

# View coverage report
# Open backend/htmlcov/index.html in browser
```

### Writing Tests

Create tests in `backend/tests/`:

```python
# backend/tests/test_my_feature.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_my_endpoint():
    response = client.get("/api/v1/my-endpoint")
    assert response.status_code == 200
    assert response.json()["message"] == "Hello from my endpoint"
```

## Code Quality

### Linting

```powershell
# Run flake8
docker-compose exec backend flake8 app/

# Run black (formatter)
docker-compose exec backend black app/

# Run mypy (type checker)
docker-compose exec backend mypy app/
```

### Pre-commit Setup

Configure pre-commit hooks for automatic checks before commits.

## Debugging

### Debugging with Logs

```powershell
# View backend logs
.\scripts\logs.ps1 -Service backend -Follow

# View all logs
.\scripts\logs.ps1 -Follow

# Docker logs directly
docker-compose logs -f backend
```

### Remote Debugging (VS Code)

Development mode exposes port 5678 for remote debugging:

1. Install `debugpy` in requirements.txt
2. Add to `backend/app/main.py`:
   ```python
   import debugpy
   debugpy.listen(("0.0.0.0", 5678))
   ```
3. Configure VS Code launch.json:
   ```json
   {
     "name": "Python: Remote Attach",
     "type": "python",
     "request": "attach",
     "connect": {
       "host": "localhost",
       "port": 5678
     }
   }
   ```

### Interactive Shell

```powershell
# Python shell with app context
docker-compose exec backend python

# IPython (if installed)
docker-compose exec backend ipython

# Database shell
docker-compose exec mysql mysql -u jerp_user -p jerp
```

## Database Management

### Accessing MySQL

```powershell
# MySQL shell
docker-compose exec mysql mysql -u jerp_user -p jerp

# Or from host (if port exposed)
mysql -h localhost -u jerp_user -p jerp
```

### Common Database Commands

```sql
-- Show tables
SHOW TABLES;

-- Describe table
DESCRIBE users;

-- Query data
SELECT * FROM users;
SELECT * FROM roles;
SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 10;

-- Count records
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM compliance_violations;
```

### Database Backups

```powershell
# Backup database
docker-compose exec mysql mysqldump -u jerp_user -p jerp > backup.sql

# Restore database
docker-compose exec -T mysql mysql -u jerp_user -p jerp < backup.sql
```

## Useful Commands

```powershell
# View running containers
docker-compose ps

# View container resources
docker stats

# Execute command in container
docker-compose exec backend python manage.py --help

# Access backend shell
docker-compose exec backend bash

# Restart specific service
docker-compose restart backend

# Rebuild and restart
docker-compose build backend
docker-compose up -d backend

# View environment variables
docker-compose exec backend printenv | grep MYSQL

# Clean up unused Docker resources
docker system prune
```

## Tips & Tricks

1. **Use VS Code Remote Containers** - Edit files directly in containers
2. **Enable Docker BuildKit** - Faster builds with caching
3. **Use `.dockerignore`** - Exclude unnecessary files from builds
4. **Keep containers running** - Faster iteration than stopping/starting
5. **Monitor resource usage** - Use `docker stats` to watch CPU/memory
6. **Use named volumes** - Persist data across container restarts
7. **Regular backups** - Backup database before major changes

## Common Issues

### Changes Not Reflected

If code changes don't take effect:

```powershell
# Restart backend
docker-compose restart backend

# Or rebuild
docker-compose build backend --no-cache
docker-compose up -d backend
```

### Database Schema Out of Sync

```powershell
# Check current migration
docker-compose exec backend alembic current

# Upgrade to latest
docker-compose exec backend alembic upgrade head
```

### Port Conflicts

If ports are already in use, update `.env`:

```env
MYSQL_PORT=3307  # Change from 3306
REDIS_PORT=6380  # Change from 6379
```

## Next Steps

- Explore [API Documentation](http://localhost:8000/api/v1/docs)
- Read [Compliance Guide](COMPLIANCE_GUIDE.md)
- Review [SOW.md](../SOW.md) for project requirements

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Docker Documentation](https://docs.docker.com/)
