"""Configuration management."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://erp_user:erp_password@localhost:5432/erp_db"
    DATABASE_URL_SYNC: str = "postgresql://erp_user:erp_password@localhost:5432/erp_db"
    
    # Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Face Recognition
    FACE_SIMILARITY_THRESHOLD: float = 0.65
    SFACE_MODEL_PATH: str = "models/sface.onnx"  # Relative to project root
    
    # Storage
    STORAGE_PATH: str = "./server/storage"
    MAX_IMAGE_SIZE_MB: int = 5
    
    # Security
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
