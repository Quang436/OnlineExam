from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application configurations.
    These variables can be overridden by environment variables or a .env file.
    """
    PROJECT_NAME: str = "Online Exam Proctoring System"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "YOUR_SUPER_SECRET_KEY"  # Nên thay đổi khi deploy
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS
    CORS_ORIGINS: Union[str, List[str]] = ["*"]
    
    # Database
    # Support both Async SQLite (for dev) and Postgres (for prod)
    DATABASE_URL: str = "sqlite+aiosqlite:///./exam_proctor.db"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

settings = Settings()
