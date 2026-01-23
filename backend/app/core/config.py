from typing import List
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "Javcore API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
    ]
    
    # Database
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATABASE_PATH: Path = BASE_DIR / "database" / "combined_videos.json"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
