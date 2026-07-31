from cryptography.fernet import Fernet

from app.core import crypto
from app.core.config import get_settings


def _reset_crypto_cache():
    crypto._get_fernet.cache_clear()
    get_settings.cache_clear()


def test_encrypt_decrypt_roundtrip_with_key(monkeypatch):
    monkeypatch.setenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    _reset_crypto_cache()
    try:
        ciphertext = crypto.encrypt("top-secret-value")
        assert ciphertext != "top-secret-value"
        assert crypto.decrypt(ciphertext) == "top-secret-value"
    finally:
        monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
        _reset_crypto_cache()


def test_without_key_falls_back_to_plaintext(monkeypatch):
    monkeypatch.setenv("ENCRYPTION_KEY", "")
    _reset_crypto_cache()
    try:
        assert crypto.encrypt("plain") == "plain"
        assert crypto.decrypt("plain") == "plain"
    finally:
        _reset_crypto_cache()


def test_decrypt_invalid_token_returns_original_instead_of_crashing(monkeypatch):
    monkeypatch.setenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    _reset_crypto_cache()
    try:
        assert crypto.decrypt("not-a-valid-fernet-token") == "not-a-valid-fernet-token"
    finally:
        monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
        _reset_crypto_cache()
