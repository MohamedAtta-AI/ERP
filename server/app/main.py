"""
OnTime ERP - FastAPI Application Entry Point

This module creates and configures the FastAPI application.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from server.config import config
from server.app.api.v1 import router as api_v1_router
from server.app.database import init_db
from server.app.middleware.error_handler import (
    global_exception_handler,
    validation_exception_handler,
    database_exception_handler,
)
from server.app.middleware.logging import StructuredLoggingMiddleware, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    print("🚀 Starting OnTime ERP API server...")
    
    # Setup logging
    setup_logging()
    
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

# Setup logging middleware (must be first)
app.add_middleware(StructuredLoggingMiddleware)

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

# Add exception handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)

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
