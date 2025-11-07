from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        populate_by_name=True,
    )

    app_name: str = "PerplexiPlay API"
    api_v1_prefix: str = "/api"
    secret_key: str = Field("dev-secret-key", alias="SECRET_KEY")
    refresh_secret_key: str = Field("dev-refresh-secret-key", alias="REFRESH_SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    database_url: str = Field("sqlite+aiosqlite:///./perplexiplay.db", alias="DATABASE_URL")
    env: Literal["dev", "prod", "test"] = Field("dev", alias="ENV")
    cors_origins: list[AnyHttpUrl] | list[str] = Field(default_factory=lambda: ["*"])


@lru_cache
def get_settings() -> Settings:
    return Settings()
