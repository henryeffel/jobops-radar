from app.core.config import Settings


def test_settings_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_name == "JobOps Radar"
    assert settings.app_env == "development"
    assert settings.debug is False
    assert settings.access_token_expire_minutes == 30
    assert settings.auth_verify_max_concurrency == 2
    assert settings.auth_verify_wait_timeout_seconds == 3
    assert settings.llm_mock_mode is True
    assert settings.llm_base_url == "https://integrate.api.nvidia.com/v1"
    assert settings.llm_timeout_seconds == 50
    assert settings.llm_max_output_tokens == 4096
    assert settings.llm_max_concurrency == 2
    assert settings.llm_wait_timeout_seconds == 1
    assert settings.cors_origins == [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ]


def test_settings_load_environment_variables(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    monkeypatch.setenv("LLM_MOCK_MODE", "false")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://jobops.example.com")

    settings = Settings(_env_file=None)

    assert settings.app_env == "test"
    assert settings.debug is True
    assert settings.access_token_expire_minutes == 60
    assert settings.llm_mock_mode is False
    assert settings.cors_origins == ["https://jobops.example.com"]
