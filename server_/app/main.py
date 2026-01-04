"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .settings import settings
from .database import init_db
from .api.v1 import employees, attendance, health
import uvicorn

app = FastAPI(
    title="ERP Face Recognition Attendance System",
    description="API for employee registration and attendance tracking with face recognition",
    version="1.0.0",
)

# CORS middleware - allow all origins in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Must be False when using "*" for origins
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await init_db()
    print("SUCCESS: Database initialized")


# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(employees.router, prefix="/api/v1")
app.include_router(attendance.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "ERP Face Recognition Attendance System API"}


if __name__ == "__main__":
    uvicorn.run(
        "server.app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )
