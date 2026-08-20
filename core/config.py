from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Online Exam Proctoring System"
    API_V1_STR: str = "/api/v1"
    
    # Database URL (Ví dụ: sqlite+aiosqlite:///./exam.db hoặc postgresql+asyncpg://user:pass@localhost:5432/exam_db)
    DATABASE_URL: str = "sqlite+aiosqlite:///./exam.db"
    
    # JWT Security
    SECRET_KEY: str = "your-super-secret-key-change-it-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 ngày
    
    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()