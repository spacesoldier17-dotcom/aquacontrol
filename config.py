from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./aqua.db"
    NOTIFICATION_SERVICE_URL: str = "http://localhost:8001/notify"

    class Config:
        env_file = ".env"

settings = Settings()