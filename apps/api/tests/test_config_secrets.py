"""F8 (docs/FIX_PLAN.md): production must refuse to start with a missing or
placeholder JWT_SECRET_KEY, instead of silently issuing forgeable tokens."""
import pytest

from app.core.config import Settings


def test_development_boots_fine_with_default_jwt_secret():
    settings = Settings(_env_file=None, ENV="development", JWT_SECRET_KEY="change-me-in-.env")
    assert settings.ENV == "development"


def test_production_rejects_default_jwt_secret():
    with pytest.raises(RuntimeError) as exc_info:
        Settings(_env_file=None, ENV="production", JWT_SECRET_KEY="change-me-in-.env")
    assert "JWT_SECRET_KEY" in str(exc_info.value)


def test_production_rejects_short_jwt_secret():
    with pytest.raises(RuntimeError) as exc_info:
        Settings(_env_file=None, ENV="production", JWT_SECRET_KEY="too-short")
    assert "JWT_SECRET_KEY" in str(exc_info.value)


def test_production_boots_with_a_real_jwt_secret():
    settings = Settings(_env_file=None, ENV="production", JWT_SECRET_KEY="a" * 64, ENCRYPTION_KEY="b" * 32)
    assert settings.ENV == "production"
