from app.core.config import Settings


def test_settings_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_name == "JobOps Radar"
    assert settings.app_env == "development"
    assert settings.debug is False
    assert settings.access_token_expire_minutes == 30
    assert settings.llm_mock_mode is True


def test_settings_load_environment_variables(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    monkeypatch.setenv("LLM_MOCK_MODE", "false")

    settings = Settings(_env_file=None)

    assert settings.app_env == "test"
    assert settings.debug is True
    assert settings.access_token_expire_minutes == 60
    assert settings.llm_mock_mode is False
