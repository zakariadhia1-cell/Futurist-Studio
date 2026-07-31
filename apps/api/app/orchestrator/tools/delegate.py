from sqlalchemy import select

from app.models.agent import Agent
from app.models.message import Message
from app.models.model_config import ModelConfig
from app.orchestrator.tool_registry import Tool, ToolContext, register


async def _delegate_to_agent(arguments: dict, ctx: ToolContext) -> str:
    agent_slug = str(arguments.get("agent_slug", "")).strip()
    task = str(arguments.get("task", "")).strip()
    if not agent_slug or not task:
        return "Sowohl agent_slug als auch task muessen angegeben werden."
    if agent_slug == "executive":
        return "Der Executive Agent kann nicht an sich selbst delegieren."

    agent = (
        await ctx.db.execute(select(Agent).where(Agent.slug == agent_slug, Agent.enabled.is_(True)))
    ).scalar_one_or_none()
    if agent is None:
        return f"Agent '{agent_slug}' existiert nicht oder ist deaktiviert."

    model_config = (
        await ctx.db.execute(select(ModelConfig).where(ModelConfig.id == agent.default_model_id))
    ).scalar_one()

    # Local import: avoids a module-level cycle (runner -> tool_registry <- this tool).
    from app.orchestrator.runner import run_agent_turn

    fake_history = [Message(conversation_id=ctx.conversation_id, role="user", content=task)]
    result = await run_agent_turn(agent, model_config.provider, model_config.model_name, fake_history, ctx)
    return f"[{agent.name}]: {result}"


register(
    Tool(
        name="delegate_to_agent",
        description=(
            "Delegiert eine Teilaufgabe an einen spezialisierten Fachagenten (z.B. 'developer', "
            "'research', 'design', 'marketing', 'automation', 'finance') und gibt dessen Antwort zurueck."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "agent_slug": {"type": "string", "description": "Slug des Zielagenten, z.B. 'developer'"},
                "task": {"type": "string", "description": "Die zu delegierende Aufgabe, in natuerlicher Sprache"},
            },
            "required": ["agent_slug", "task"],
        },
        handler=_delegate_to_agent,
    )
)
