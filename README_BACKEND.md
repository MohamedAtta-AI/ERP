# Backend Setup Instructions

## Prerequisites

1. **Docker Desktop** - Must be installed and running
2. **Python 3.10+** with `uv` package manager
3. **PostgreSQL with pgvector** (via Docker)

## Quick Start

### 1. Start Docker Desktop

Make sure Docker Desktop is running before proceeding.

### 2. Start Database

```bash
docker-compose up -d
```

This will start PostgreSQL with pgvector extension on port 5432.

### 3. Setup Database Tables

```bash
python setup_db.py
```

This will:

- Enable pgvector extension
- Create all necessary tables (employees, face_embeddings, attendance)

### 4. Start Backend Server

```bash
python start_backend.py
```

Or manually:

```bash
uvicorn server.app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will be available at:

- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health

## Database Configuration

Default database credentials (from docker-compose.yml):

- Host: localhost
- Port: 5432
- Database: erp_db
- User: erp_user
- Password: erp_password

To change these, update `docker-compose.yml` and `server/app/config.py`.

## Troubleshooting

### Docker Desktop not running

- Start Docker Desktop manually
- Wait for it to fully start (check system tray)
- Verify with: `docker ps`

### Database connection errors

- Check if container is running: `docker ps`
- Check container logs: `docker-compose logs postgres`
- Verify database is ready: `docker-compose ps`

### Port already in use

- Change port in `docker-compose.yml` (for database)
- Change `API_PORT` in `server/app/config.py` (for backend)

## Environment Variables

Create a `.env` file in the project root (optional, defaults are in config.py):

```env
DATABASE_URL=postgresql+asyncpg://erp_user:erp_password@localhost:5432/erp_db
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

## Anti-spoofing (DeepFace)

The backend uses **DeepFace** for lightweight, real-time anti-spoofing detection. DeepFace's anti-spoofing module automatically detects if a face is real or fake (spoofed).

### Installation

DeepFace is included in the project dependencies. Install with:

```bash
uv sync
```

**Note:** DeepFace requires Python 3.10-3.13 (TensorFlow dependency limitation). The project is configured for `requires-python = ">=3.10,<3.14"`.

### How It Works

- DeepFace's anti-spoofing is optimized for real-time use
- It automatically downloads required models on first use (stored in `~/.deepface/weights/`)
- Works with pre-cropped 112×112 face images from the frontend
- Uses OpenCV detector backend for lightweight, fast processing
- Returns a simple boolean: `is_real` (True = live face, False = spoof)

### Model Download

DeepFace will automatically download anti-spoofing models on first use. No manual download required. Models are cached locally for subsequent runs.

**Previous Implementation:**
The old MiniFASNet implementation has been replaced with DeepFace for better real-time performance and easier maintenance.
