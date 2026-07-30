"""Seeds baseline reference data (roles, model configs, the Executive Agent). Safe to run
repeatedly - existing rows are left untouched."""
import asyncio

from sqlalchemy import select

from app.db.base import async_session_factory
from app.models.agent import Agent
from app.models.model_config import ModelConfig
from app.models.role import Role

ROLES = [
    ("admin", "Administrator"),
    ("member", "Mitglied"),
]

# Model IDs are configuration, not code - adjust freely as providers ship new versions.
MODEL_CONFIGS = [
    {
        "provider": "anthropic",
        "model_name": "claude-haiku-4-5-20251001",
        "display_name": "Claude Haiku 4.5",
        "capabilities": {"tools": True, "vision": True},
        "is_default": True,
    },
    {
        "provider": "openai",
        "model_name": "gpt-4.1-mini",
        "display_name": "GPT-4.1 Mini",
        "capabilities": {"tools": True, "vision": True},
        "is_default": False,
    },
    {
        "provider": "ollama",
        "model_name": "llama3.1",
        "display_name": "Llama 3.1 (lokal via Ollama)",
        "capabilities": {"tools": False, "vision": False},
        "is_default": False,
    },
]

EXECUTIVE_SYSTEM_PROMPT = """Du bist der Executive Agent von FUTURIST OS, dem persoenlichen \
KI-Betriebssystem von Z. Du planst Aufgaben, priorisierst Projekte und bist der erste \
Ansprechpartner fuer alles. Antworte klar, knapp und auf Deutsch. Delegation an \
Fachagenten (Developer, Design, Marketing, Research, Automation, Finance) kommt in einer \
spaeteren Ausbaustufe - bis dahin beantwortest du Anfragen direkt."""


async def seed_roles(db) -> None:
    for slug, name in ROLES:
        existing = await db.execute(select(Role).where(Role.slug == slug))
        if existing.scalar_one_or_none() is None:
            db.add(Role(slug=slug, name=name))
            print(f"Rolle angelegt: {slug}")


async def seed_model_configs(db) -> ModelConfig:
    default_config: ModelConfig | None = None
    for cfg in MODEL_CONFIGS:
        existing = await db.execute(
            select(ModelConfig).where(
                ModelConfig.provider == cfg["provider"], ModelConfig.model_name == cfg["model_name"]
            )
        )
        model_config = existing.scalar_one_or_none()
        if model_config is None:
            model_config = ModelConfig(**cfg)
            db.add(model_config)
            await db.flush()
            print(f"Modell-Konfiguration angelegt: {cfg['display_name']}")
        if cfg["is_default"]:
            default_config = model_config
    return default_config


async def seed_executive_agent(db, default_model: ModelConfig) -> None:
    existing = await db.execute(select(Agent).where(Agent.slug == "executive"))
    if existing.scalar_one_or_none() is None:
        db.add(
            Agent(
                slug="executive",
                name="Executive Agent",
                description="Plant Aufgaben, priorisiert Projekte, koordiniert Fachagenten.",
                system_prompt=EXECUTIVE_SYSTEM_PROMPT,
                default_model_id=default_model.id,
                config={},
                enabled=True,
            )
        )
        print("Agent angelegt: executive")


async def seed_all() -> None:
    async with async_session_factory() as db:
        await seed_roles(db)
        await db.flush()
        default_model = await seed_model_configs(db)
        await db.flush()
        await seed_executive_agent(db, default_model)
        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed_all())
