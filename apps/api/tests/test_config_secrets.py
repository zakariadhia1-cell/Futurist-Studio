"""F8/F9 (docs/FIX_PLAN.md): production must refuse to start with a missing/placeholder
JWT_SECRET_KEY or a missing ENCRYPTION_KEY, instead of silently running insecurely."""
import pytest

from app.core.config import Settings


def test_development_boots_fine_with_no_secrets_configured():
    settings = Settings(_env_file=None, ENV="development", JWT_SECRET_KEY="change-me-in-.env", ENCRYPTION_KEY="")
    assert settings.ENV == "development"


def test_production_rejects_default_jwt_secret_and_missing_encryption_key():
    with pytest.raises(RuntimeError) as exc_info:
        Settings(_env_file=None, ENV="production", JWT_SECRET_KEY="change-me-in-.env", ENCRYPTION_KEY="")
    message = str(exc_info.value)
    assert "JWT_SECRET_KEY" in message
    assert "ENCRYPTION_KEY" in message


def test_production_rejects_short_jwt_secret():
    with pytest.raises(RuntimeError) as exc_info:
        Settings(_env_file=None, ENV="production", JWT_SECRET_KEY="too-short", ENCRYPTION_KEY="a" * 32)
    assert "JWT_SECRET_KEY" in str(exc_info.value)


def test_production_rejects_missing_encryption_key_alone():
    with pytest.raises(RuntimeError) as exc_info:
        Settings(_env_file=None, ENV="production", JWT_SECRET_KEY="a" * 64, ENCRYPTION_KEY="")
    assert "ENCRYPTION_KEY" in str(exc_info.value)


def test_production_boots_with_real_secrets_configured():
    settings = Settings(_env_file=None, ENV="production", JWT_SECRET_KEY="a" * 64, ENCRYPTION_KEY="b" * 32)
    assert settings.ENV == "production"
