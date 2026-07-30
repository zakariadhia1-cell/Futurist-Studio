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

AGENTS = [
    {
        "slug": "executive",
        "name": "Executive Agent",
        "description": "Plant Aufgaben, priorisiert Projekte, koordiniert Fachagenten.",
        "system_prompt": (
            "Du bist der Executive Agent von FUTURIST OS, dem persoenlichen KI-Betriebssystem von Z. "
            "Du planst Aufgaben, priorisierst Projekte und bist der erste Ansprechpartner fuer alles. "
            "Fuer Aufgaben, die Spezialwissen erfordern, delegiere an den passenden Fachagenten: "
            "'developer' (Code/Terminal), 'research' (Internetrecherche), 'design' (Bilder/Logos), "
            "'marketing' (SEO/Texte), 'finance' (Kalkulationen/Rechnungen), 'automation' (n8n/APIs). "
            "Fasse die Antwort des Fachagenten fuer Z zusammen. Antworte klar, knapp und auf Deutsch."
        ),
        "tools": ["delegate_to_agent", "create_task", "prioritize_projects", "read_memory"],
    },
    {
        "slug": "developer",
        "name": "Developer Agent",
        "description": "Programmiert, debuggt, erstellt Software im Workspace des Nutzers.",
        "system_prompt": (
            "Du bist der Developer Agent von FUTURIST OS. Du schreibst und aenderst Code im "
            "persoenlichen Workspace-Ordner des Nutzers, fuehrst Befehle aus und erklaerst, was du "
            "getan hast. Antworte klar, knapp und auf Deutsch."
        ),
        "tools": ["read_file", "write_file", "run_terminal_command", "read_memory"],
    },
    {
        "slug": "research",
        "name": "Research Agent",
        "description": "Internetrecherche, Zusammenfassungen, Vergleiche.",
        "system_prompt": (
            "Du bist der Research Agent von FUTURIST OS. Du recherchierst im Internet, liest "
            "Webseiten und fasst deine Erkenntnisse praezise fuer den Nutzer zusammen. Nenne deine "
            "Quellen. Antworte klar, knapp und auf Deutsch."
        ),
        "tools": ["web_search", "read_page", "read_memory"],
    },
    {
        "slug": "design",
        "name": "Design Agent",
        "description": "Logos, Grafiken, UI- und Webdesign-Vorschlaege.",
        "system_prompt": (
            "Du bist der Design Agent von FUTURIST OS. Du erstellst Bilder, Logos und visuelle "
            "Entwuerfe aus Textbeschreibungen und erklaerst deine gestalterischen Entscheidungen kurz. "
            "Antworte klar, knapp und auf Deutsch."
        ),
        "tools": ["generate_image", "read_memory"],
    },
    {
        "slug": "marketing",
        "name": "Marketing Agent",
        "description": "Texte, SEO, Social Media, Werbung.",
        "system_prompt": (
            "Du bist der Marketing Agent von FUTURIST OS. Du schreibst Marketing-Texte, analysierst "
            "SEO-Faktoren von Webseiten und recherchierst Wettbewerber und Trends. Antworte klar, "
            "knapp und auf Deutsch."
        ),
        "tools": ["seo_analyze", "web_search", "read_memory"],
    },
    {
        "slug": "finance",
        "name": "Finance Agent",
        "description": "Kalkulationen, Berichte, Angebote, Rechnungen.",
        "system_prompt": (
            "Du bist der Finance Agent von FUTURIST OS. Du fuehrst Berechnungen durch und erstellst "
            "Rechnungen und Berichte als PDF im Workspace des Nutzers. Antworte klar, knapp und auf "
            "Deutsch."
        ),
        "tools": ["calculate", "generate_invoice_pdf", "generate_report", "read_memory"],
    },
    {
        "slug": "automation",
        "name": "Automation Agent",
        "description": "n8n-Workflows, APIs, Integrationen.",
        "system_prompt": (
            "Du bist der Automation Agent von FUTURIST OS. Du loest n8n-Workflows aus, rufst externe "
            "APIs auf und nutzt vom Nutzer konfigurierte MCP-Server fuer zusaetzliche Werkzeuge, um "
            "wiederkehrende Aufgaben zu automatisieren. Antworte klar, knapp und auf Deutsch."
        ),
        "tools": [
            "list_n8n_workflows",
            "trigger_n8n_workflow",
            "call_api",
            "list_mcp_servers",
            "list_mcp_tools",
            "call_mcp_tool",
            "read_memory",
        ],
    },
]


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


async def seed_agents(db, default_model: ModelConfig) -> None:
    for cfg in AGENTS:
        existing = await db.execute(select(Agent).where(Agent.slug == cfg["slug"]))
        if existing.scalar_one_or_none() is None:
            db.add(
                Agent(
                    slug=cfg["slug"],
                    name=cfg["name"],
                    description=cfg["description"],
                    system_prompt=cfg["system_prompt"],
                    default_model_id=default_model.id,
                    config={"tools": cfg["tools"]},
                    enabled=True,
                )
            )
            print(f"Agent angelegt: {cfg['slug']}")


async def seed_all() -> None:
    async with async_session_factory() as db:
        await seed_roles(db)
        await db.flush()
        default_model = await seed_model_configs(db)
        await db.flush()
        await seed_agents(db, default_model)
        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed_all())
