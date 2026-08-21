from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Online Exam Proctoring System"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = "YOUR_SUPER_SECRET_KEY"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    
    CORS_ORIGINS: Union[str, List[str]] = ["*"]
    DATABASE_URL: str = "sqlite+aiosqlite:///./exam.db"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True)

settings = Settings()