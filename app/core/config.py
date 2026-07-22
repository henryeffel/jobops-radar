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
    jwt_secret_key: str = "local-only-change-me-32-bytes-minimum"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    auth_verify_max_concurrency: int = 2
    auth_verify_wait_timeout_seconds: float = 3
    saramin_access_key: str = ""
    saramin_api_base_url: str = "https://oapi.saramin.co.kr"
    llm_api_key: str = ""
    llm_mock_mode: bool = True
    llm_base_url: str = "https://integrate.api.nvidia.com/v1"
    llm_model: str = "nvidia/nemotron-3-ultra-550b-a55b"
    llm_timeout_seconds: float = 50
    llm_max_input_chars: int = 30_000
    llm_max_output_tokens: int = 4_096
    llm_max_concurrency: int = 2
    llm_wait_timeout_seconds: float = 1
    cors_allowed_origins: str = (
        "http://127.0.0.1:5173,http://localhost:5173"
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
