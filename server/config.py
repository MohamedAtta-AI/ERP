from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Union
from pathlib import Path


class Config(BaseSettings):
    """Application settings loaded from environment variables."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PRODUCTION: bool = False

    # Database Configuration
    DB_URL: str = (
        "postgresql://erp_user:erp_password@localhost:5432/erp_db"
    )

    # Server Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:5173", "http://localhost:3000"]
    CORS_CREDENTIALS: bool = False
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from comma-separated string if needed."""
        if isinstance(v, str):
            # Split comma-separated string and strip whitespace
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Face Recognition Configuration
    RECOGNITION_MODEL_PATH: str = "models/facenet128.onnx"
    RECOGNITION_MODEL_NAME: str = "Facenet"
    SIMILARITY_THRESHOLD: float = 0.60
    EMBEDDING_SIZE: int = 128

    ANTISPOOF_MODEL_PATH: str = "models/sface.onnx"
    
    # JWT Configuration
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ACCESS_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 7


config = Config()