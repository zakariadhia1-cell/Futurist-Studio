"""Central application settings, loaded from environment variables (.env)."""
import os
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_API_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The literal default below - kept for local dev/test convenience, where an unset
# JWT_SECRET_KEY should still let the app boot. _enforce_production_secrets() below
# refuses to start with this value (or anything shorter than _MIN_SECRET_LENGTH) once
# ENV=production - see F8 in docs/FIX_PLAN.md.
_INSECURE_JWT_DEFAULT = "change-me-in-.env"
_MIN_SECRET_LENGTH = 32


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
    JWT_SECRET_KEY: str = _INSECURE_JWT_DEFAULT
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # --- Secrets encryption (Fernet key for encrypting stored API keys) ---
    ENCRYPTION_KEY: str = ""

    # --- Model providers ---
    # Server-wide keys are enough to exercise the abstraction end to end for a
    # single-admin deployment; per-user encrypted provider keys would be a genuine
    # multi-tenant feature, out of scope for the Phase 0 single-user assumption. Secrets
    # that *are* user-supplied and stored in the DB (MCP server env vars, Phase 9) are
    # encrypted at rest via ENCRYPTION_KEY - see app/core/crypto.py.
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

    # --- Files (Phase 7) ---
    # Every user gets a subdirectory here; uploaded/generated files are stored under a
    # random key (not the original filename) to rule out path traversal entirely.
    FILES_DIR: str = os.path.join(_API_ROOT, "storage", "files")
    MAX_FILE_SIZE_BYTES: int = 25 * 1024 * 1024

    # --- Google OAuth: Calendar/E-Mail (Phase 7) ---
    # Genuinely optional - unset, the /integrations/google endpoints and Calendar/Gmail
    # tools just report "not configured" instead of failing. Redirect URI must exactly
    # match what's registered in the Google Cloud Console OAuth client.
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # --- Observability (Phase 9) ---
    # Genuinely optional: unset, the app just logs structured JSON to stdout.
    SENTRY_DSN: str = ""

    @model_validator(mode="after")
    def _enforce_production_secrets(self) -> "Settings":
        """Fail loudly at startup instead of quietly running with forgeable auth
        tokens or plaintext-stored secrets in production (F8/F9 in docs/FIX_PLAN.md -
        S8/S9 in docs/AUDIT_REPORT.md). Dev/test are unaffected: this only fires when
        ENV=production, so the convenience defaults above still work locally.

        F9 is enforced here rather than in app/core/crypto.py because this validator
        runs once at Settings construction (i.e. real app startup, via main.py's
        `settings = get_settings()`), matching the fix plan's own "same
        startup-validation approach as F8" - crypto.py's encrypt()/decrypt() are called
        lazily per-request and have no natural startup hook of their own. Once this
        check passes, ENCRYPTION_KEY is guaranteed non-empty, so crypto.py's plaintext
        fallback path (see its own docstring) is dead code in production - it stays in
        place only as the dev/test convenience it's documented to be."""
        if self.ENV != "production":
            return self

        problems: list[str] = []
        if (
            not self.JWT_SECRET_KEY
            or self.JWT_SECRET_KEY == _INSECURE_JWT_DEFAULT
            or len(self.JWT_SECRET_KEY) < _MIN_SECRET_LENGTH
        ):
            problems.append(
                f"JWT_SECRET_KEY fehlt, ist der unsichere Platzhalter, oder kuerzer als "
                f"{_MIN_SECRET_LENGTH} Zeichen. Erzeugen mit: openssl rand -hex 32"
            )
        if not self.ENCRYPTION_KEY:
            problems.append(
                "ENCRYPTION_KEY fehlt - gespeicherte Secrets (MCP-Server-Umgebungsvariablen, "
                "Google-OAuth-Tokens) wuerden im Klartext abgelegt. Erzeugen mit: "
                'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
            )
        if problems:
            raise RuntimeError(
                "Unsichere Konfiguration fuer ENV=production - Start abgebrochen:\n- " + "\n- ".join(problems)
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
