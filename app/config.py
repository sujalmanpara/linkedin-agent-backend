from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/linkedin_agent"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Encryption
    ENCRYPTION_KEY: str = ""

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # Sync mode (for testing without Celery/Redis)
    SYNC_MODE: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
