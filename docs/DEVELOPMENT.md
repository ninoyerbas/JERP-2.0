# JERP 2.0 - Development Guide

## Development Setup

This guide covers local development setup for JERP 2.0.

## Prerequisites

- Python 3.11+
- MySQL 8.0
- Redis 7+
- Git

## Local Development (Without Docker)

### 1. Clone Repository

```bash
git clone https://github.com/ninoyerbas/JERP-2.0.git
cd JERP-2.0
```

### 2. Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example env file
cp ../.env.example ../.env

# Edit with your local database settings
# Set MYSQL_HOST=localhost
```

### 5. Set Up Local Database

**Windows (PowerShell):**
```powershell
# Start MySQL if not running
mysql -u root -p

# In MySQL shell:
CREATE DATABASE jerp;
CREATE USER 'jerp_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON jerp.* TO 'jerp_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 6. Run Migrations

```bash
# From backend directory
alembic upgrade head
```

### 7. Initialize Database

```bash
python scripts/init_db.py
```

### 8. Start Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit http://localhost:8000/api/v1/docs for API documentation.

## Development with Docker

### Start Development Environment

```powershell
docker-compose up
```

The `docker-compose.yml` file is configured for development with:
- Hot reload enabled
- Volume mounts for code changes
- Debug logging enabled

### Access Development Services

- Backend: http://localhost:8000
- MySQL: localhost:3306
- Redis: localhost:6379

### Connect to Services

**Backend Shell:**
```powershell
docker-compose exec backend sh
```

**MySQL Shell:**
```powershell
docker-compose exec mysql mysql -u jerp_user -p
```

**Redis CLI:**
```powershell
docker-compose exec redis redis-cli
```

## Database Migrations

### Create a New Migration

```bash
cd backend
alembic revision --autogenerate -m "description of changes"
```

Review the generated migration file in `backend/alembic/versions/` before applying.

### Apply Migrations

```bash
alembic upgrade head
```

### Rollback Migration

```bash
# Rollback one version
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>
```

### View Migration History

```bash
alembic history
alembic current
```

## Testing

### Run All Tests

```bash
cd backend
pytest
```

### Run Specific Test File

```bash
pytest tests/test_health.py
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

View coverage report at `htmlcov/index.html`

### Run Tests in Docker

```powershell
docker-compose exec backend pytest
```

## Code Quality

### Format Code

```bash
cd backend
black app/ tests/
```

### Lint Code

```bash
flake8 app/ tests/
```

### Type Checking

```bash
mypy app/
```

### Run All Quality Checks

```bash
black app/ tests/ && flake8 app/ tests/ && mypy app/
```

## Project Structure

```
JERP-2.0/
├── backend/
│   ├── alembic/              # Database migrations
│   │   └── versions/         # Migration files
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   │   └── v1/           # API version 1
│   │   ├── core/             # Core functionality
│   │   │   ├── config.py     # Configuration
│   │   │   ├── database.py   # Database connection
│   │   │   ├── security.py   # Security utilities
│   │   │   └── deps.py       # Dependencies
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   └── main.py           # Application entry
│   ├── scripts/              # Utility scripts
│   ├── tests/                # Test files
│   ├── alembic.ini           # Alembic configuration
│   └── requirements.txt      # Python dependencies
├── docs/                     # Documentation
├── scripts/                  # Deployment scripts
├── docker-compose.yml        # Docker Compose config
├── Dockerfile                # Docker image definition
└── .env.example              # Environment template
```

## API Development

### Adding a New Endpoint

1. **Define Schema** (`backend/app/schemas/`)
   ```python
   from pydantic import BaseModel
   
   class MyResourceCreate(BaseModel):
       name: str
       description: str
   ```

2. **Create Model** (`backend/app/models/`)
   ```python
   from sqlalchemy import Column, String, Integer
   from app.core.database import Base
   
   class MyResource(Base):
       __tablename__ = "my_resources"
       id = Column(Integer, primary_key=True)
       name = Column(String(255))
   ```

3. **Create Migration**
   ```bash
   alembic revision --autogenerate -m "add my_resource table"
   alembic upgrade head
   ```

4. **Add Endpoint** (`backend/app/api/v1/endpoints/`)
   ```python
   from fastapi import APIRouter, Depends
   from sqlalchemy.orm import Session
   from app.core.database import get_db
   
   router = APIRouter()
   
   @router.post("/my-resources")
   def create_resource(
       resource: MyResourceCreate,
       db: Session = Depends(get_db)
   ):
       # Implementation
       pass
   ```

5. **Register Router** (in `backend/app/api/v1/router.py`)

6. **Write Tests** (`backend/tests/test_api/`)

## Database Models

### Best Practices

- Use `sa.DateTime` with `default=datetime.utcnow` for timestamps
- Always include `created_at` and `updated_at` fields
- Use proper indexes for frequently queried fields
- Define relationships clearly
- Use enums for fixed choice fields

### Example Model

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from app.core.database import Base

class ExampleModel(Base):
    __tablename__ = "examples"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

## Environment Variables

Development `.env` configuration:

```env
APP_ENV=development
APP_DEBUG=true
MYSQL_HOST=localhost          # localhost for local dev
MYSQL_PORT=3306
MYSQL_DATABASE=jerp
MYSQL_USER=jerp_user
MYSQL_PASSWORD=dev_password
JWT_SECRET_KEY=dev_secret_key_not_for_production
```

## Debugging

### VS Code Launch Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
      ],
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      },
      "console": "integratedTerminal"
    }
  ]
}
```

### Enable Debug Logging

In `.env`:
```env
APP_DEBUG=true
```

This enables SQLAlchemy query logging and detailed error messages.

## Contributing

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make your changes
3. Run tests: `pytest`
4. Run code quality checks: `black . && flake8 . && mypy app/`
5. Commit your changes: `git commit -am 'Add new feature'`
6. Push to the branch: `git push origin feature/my-feature`
7. Create a Pull Request

## Common Tasks

### Reset Development Database

```bash
# With Docker
docker-compose down -v
docker-compose up -d

# Without Docker
mysql -u root -p -e "DROP DATABASE jerp; CREATE DATABASE jerp;"
alembic upgrade head
python scripts/init_db.py
```

### Add a New Python Dependency

```bash
# Install package
pip install package-name

# Update requirements.txt
pip freeze > requirements.txt

# Or manually add to requirements.txt with version
```

### View Database Schema

```bash
# With Docker
docker-compose exec mysql mysql -u jerp_user -p jerp

# In MySQL shell
SHOW TABLES;
DESCRIBE table_name;
```

## Resources

- FastAPI Documentation: https://fastapi.tiangolo.com/
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- Alembic Documentation: https://alembic.sqlalchemy.org/
- Pydantic Documentation: https://docs.pydantic.dev/

## Getting Help

- Check existing issues on GitHub
- Review API documentation at `/api/v1/docs`
- Read the [COMPLIANCE_GUIDE.md](COMPLIANCE_GUIDE.md) for compliance-specific development
