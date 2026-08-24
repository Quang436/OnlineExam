from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Online Exam Proctoring WebSocket"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    JWT_SECRET: str = "TAMP_SECRET_333333333"
    GEMINI_API_KEY: str = "AIzaSyB-0MPTUSAIzaSyB-0MPTUS_YfffLHvTZuPDTCo7YVjvs5HU" # Người dùng sẽ cài qua .env hoặc truyền vào container
    
    SECRET_KEY: str = "YOUR_SUPER_SECRET_KEY"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    
    CORS_ORIGINS: Union[str, List[str]] = ["*"]
    DATABASE_URL: str = "sqlite+aiosqlite:///./exam.db"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True)

settings = Settings()