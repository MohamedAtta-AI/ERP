"""Start backend server and database."""
import subprocess
import sys
import time
import os
from pathlib import Path


def check_docker():
    """Check if Docker is running."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def start_database():
    """Start PostgreSQL database using docker-compose."""
    print("Starting PostgreSQL database with pgvector...")
    
    if not check_docker():
        print("ERROR: Docker Desktop is not running!")
        print("   Please start Docker Desktop and try again.")
        return False
    
    try:
        # Start database container
        result = subprocess.run(
            ["docker-compose", "up", "-d"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("SUCCESS: Database container started successfully!")
            print("   Waiting for database to be ready...")
            time.sleep(5)
            return True
        else:
            print(f"ERROR: Failed to start database: {result.stderr}")
            return False
    except Exception as e:
        print(f"ERROR: Error starting database: {e}")
        return False


def setup_database():
    """Setup database tables."""
    print("\nSetting up database tables...")
    try:
        result = subprocess.run(
            [sys.executable, "setup_db.py"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(f"ERROR: Database setup failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"ERROR: Error setting up database: {e}")
        return False


def start_server():
    """Start FastAPI server."""
    print("\nStarting FastAPI server...")
    print("   Server will be available at http://localhost:8000")
    print("   API docs available at http://localhost:8000/docs")
    print("\n   Press Ctrl+C to stop the server\n")
    
    try:
        # Use uv run to ensure correct environment
        subprocess.run(
            ["uv", "run", "uvicorn", "server.app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            cwd=Path(__file__).parent
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped")
    except Exception as e:
        print(f"ERROR: Error starting server: {e}")


def main():
    """Main function."""
    print("=" * 60)
    print("  ERP Face Recognition Attendance System - Backend")
    print("=" * 60)
    
    # Start database
    if not start_database():
        print("\nWARNING: Database not started. Continuing anyway...")
        print("   Make sure PostgreSQL is running on localhost:5432")
    
    # Setup database
    setup_database()
    
    # Start server
    start_server()


if __name__ == "__main__":
    main()
