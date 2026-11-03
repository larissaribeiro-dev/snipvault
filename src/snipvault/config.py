from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEY = "dev-only-insecure-key-change-me-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SNIPVAULT_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./snipvault.db"
    secret_key: str = DEFAULT_SECRET_KEY
    algorithm: str = "HS256"
    access_token_minutes: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
