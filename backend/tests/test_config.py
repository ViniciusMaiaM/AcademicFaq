import pytest
from core.config import Settings, settings
from pydantic import ValidationError


def test_settings_import_does_not_crash_with_extra_env_vars(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-3.5-turbo")
    Settings()


def test_cors_rejects_wildcard_origin_with_credentials():
    with pytest.raises(ValidationError):
        Settings(ALLOW_ORIGINS=["*"], ALLOW_CREDENTIALS=True)


def test_cors_allows_wildcard_origin_without_credentials():
    s = Settings(ALLOW_ORIGINS=["*"], ALLOW_CREDENTIALS=False)
    assert s.ALLOW_ORIGINS == ["*"]


def test_default_settings_do_not_allow_insecure_cors():
    assert not (settings.ALLOW_CREDENTIALS and "*" in settings.ALLOW_ORIGINS)
