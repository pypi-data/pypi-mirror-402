from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PREFIX = "xmas_"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        env_prefix=ENV_PREFIX,
        env_file=".env",
        env_file_encoding="utf-8",
    )

    db_srid: int = 25832
    db_schema: str | None = None
    db_views: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
