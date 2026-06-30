from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "JobOps Radar"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = False
    database_url: str = (
        "postgresql+psycopg://jobops:jobops@localhost:5432/jobops"
    )
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    saramin_access_key: str = ""
    saramin_api_base_url: str = "https://oapi.saramin.co.kr"
    llm_api_key: str = ""
    llm_mock_mode: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
