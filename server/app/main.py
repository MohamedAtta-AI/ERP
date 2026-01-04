"""
OnTime ERP - FastAPI Application Entry Point

This module creates and configures the FastAPI application.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.config import config
from server.app.api.v1 import router as api_v1_router
from server.app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    print("🚀 Starting OnTime ERP API server...")
    
    # Initialize database
    try:
        await init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")
    
    yield
    
    # Shutdown
    print("👋 Shutting down OnTime ERP API server...")


app = FastAPI(
    title="OnTime ERP",
    description="Attendance + Payroll Management System with Face Recognition",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
print(f"🌐 CORS Configuration:")
print(f"   Allowed Origins: {config.CORS_ORIGINS}")
print(f"   Allow Credentials: {config.CORS_CREDENTIALS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=config.CORS_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_v1_router)


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for Docker and load balancer probes.
    
    Returns:
        dict: Health status information
    """
    return {
        "status": "healthy",
        "service": "ontime-erp-api",
        "version": "0.1.0",
    }


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    
    Returns:
        dict: API welcome message and documentation links
    """
    return {
        "message": "Welcome to OnTime ERP API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }
