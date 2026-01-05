# OnTime ERP - Attendance & Payroll Management System

A comprehensive ERP system for attendance tracking with face recognition and payroll management.

## Features

- **Face Recognition Attendance**: Biometric check-in/check-out using DeepFace
- **Payroll Management**: Complete payroll calculation with advances, loans, insurance, and tax
- **Role-Based Access Control**: Admin, Supervisor, and Worker roles with granular permissions
- **Multi-Location Support**: Manage multiple work locations/clients
- **Comprehensive Reporting**: Attendance and payroll reports with PDF/Excel export
- **Bank Transfer Files**: Generate CSV/Excel files for bank transfers
- **Payslip Generation**: Arabic and English payslip PDFs
- **Audit Logging**: Complete audit trail for all changes

## Architecture

- **Backend**: FastAPI (Python) with async SQLAlchemy
- **Frontend**: React 18 with Vite
- **Database**: PostgreSQL with pgvector extension
- **Authentication**: JWT tokens with refresh mechanism
- **Migrations**: Alembic for database schema management

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.10+ (for local development)
- Node.js 18+ (for frontend development)

### Using Docker Compose

1. Clone the repository:
```bash
git clone <repository-url>
cd ERP
```

2. Create `.env` file from `.env.example`:
```bash
cp .env.example .env
# Edit .env and set your JWT_SECRET_KEY and database credentials
```

3. Start services:
```bash
docker-compose up -d
```

4. Run database migrations:
```bash
docker-compose exec backend uv run alembic upgrade head
```

5. Access the application:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Local Development

#### Backend Setup

1. Install dependencies:
```bash
uv sync
```

2. Set up environment variables (create `.env` file):
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run database migrations:
```bash
uv run alembic upgrade head
```

4. Start the development server:
```bash
uv run uvicorn server.app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

1. Install dependencies:
```bash
cd client
npm install
```

2. Start development server:
```bash
npm run dev
```

## Environment Variables

See `.env.example` for all available environment variables:

- `DB_URL`: PostgreSQL database connection string
- `JWT_SECRET_KEY`: Secret key for JWT token signing (required in production)
- `JWT_ACCESS_EXPIRE_MINUTES`: Access token expiration (default: 15)
- `JWT_REFRESH_EXPIRE_DAYS`: Refresh token expiration (default: 7)
- `CORS_ORIGINS`: Comma-separated list of allowed CORS origins
- `PRODUCTION`: Set to `true` in production environment

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Database Migrations

Migrations are managed using Alembic:

```bash
# Create a new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1
```

## Testing

### Backend Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=server --cov-report=html
```

### Frontend Tests

```bash
cd client
npm test
```

## Deployment

### Production Checklist

1. Set `PRODUCTION=true` in environment variables
2. Set a strong `JWT_SECRET_KEY`
3. Configure proper `CORS_ORIGINS`
4. Use secure database credentials
5. Enable SSL/TLS for API endpoints
6. Set up proper logging and monitoring
7. Configure backup strategy for database

### Docker Production Build

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Project Structure

```
ERP/
├── server/                 # Backend application
│   ├── app/
│   │   ├── api/v1/        # API endpoints
│   │   ├── services/       # Business logic
│   │   ├── middleware/     # Middleware (logging, error handling)
│   │   └── dependencies.py # FastAPI dependencies
│   ├── db/
│   │   └── models.py       # SQLModel database models
│   └── config.py           # Configuration
├── client/                 # Frontend application
│   └── src/
├── alembic/                # Database migrations
│   └── versions/
├── tests/                  # Test files
├── docker-compose.yml      # Docker Compose configuration
└── README.md
```

## Role-Based Access Control

### Admin
- Full access to all features
- Can register supervisors
- Can manage locations, payroll, reports
- Can create salary components, advances, loans
- Can approve payroll runs

### Supervisor
- Can register/edit workers (non-monetary fields only)
- Can take attendance (self + workers)
- Can manage overtime for workers
- Read-only access to master data

### Worker
- No UI interface
- Access via supervisor/admin views only
- Can view own payslips and attendance

## License

[Your License Here]

## Support

For issues and questions, please open an issue on the repository.
