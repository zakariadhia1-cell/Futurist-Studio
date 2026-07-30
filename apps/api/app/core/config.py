"""Central application settings, loaded from environment variables (.env)."""
import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

_API_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    APP_NAME: str = "FUTURIST OS"
    ENV: str = "development"
    DEBUG: bool = True

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://futurist:futurist@localhost:5432/futurist_os"

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Auth / JWT ---
    JWT_SECRET_KEY: str = "change-me-in-.env"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # --- Secrets encryption (Fernet key for encrypting stored API keys) ---
    ENCRYPTION_KEY: str = ""

    # --- Model providers ---
    # Per-user encrypted keys (app.core.config.ENCRYPTION_KEY) land in Phase 9; for now a
    # single set of server-wide keys is enough to exercise the abstraction end to end.
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # --- CORS ---
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # --- Developer Agent sandbox ---
    # Every user gets a subdirectory here; read_file/write_file/run_terminal_command are
    # confined to it (no access to the rest of the container's filesystem).
    WORKSPACES_DIR: str = os.path.join(_API_ROOT, "workspaces")

    # --- Browser automation (Phase 4) ---
    # Leave unset to let Playwright resolve its own installed browser; only needed for a
    # pre-provisioned binary in a nonstandard location.
    PLAYWRIGHT_EXECUTABLE_PATH: str = ""

    # --- Automation Agent / n8n (Phase 5) ---
    N8N_BASE_URL: str = ""
    N8N_API_KEY: str = ""

    # --- Voice (Phase 6) ---
    # STT reuses OPENAI_API_KEY (Whisper). TTS is ElevenLabs, genuinely optional - the
    # frontend falls back to the browser's own speechSynthesis when unset.
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"


@lru_cache
def get_settings() -> Settings:
    return Settings()
