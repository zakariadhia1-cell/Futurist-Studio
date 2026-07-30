import uuid

from sqlalchemy import select

from app.models.project import Project
from app.models.task import Task
from app.orchestrator.tool_registry import Tool, ToolContext, register


async def _create_task(arguments: dict, ctx: ToolContext) -> str:
    title = str(arguments.get("title", "")).strip()
    if not title:
        return "Kein Titel angegeben."

    project_id_raw = arguments.get("project_id")
    project_id = None
    if project_id_raw:
        try:
            project_id = uuid.UUID(str(project_id_raw))
        except ValueError:
            return f"Ungueltige project_id: '{project_id_raw}'"
        project = (
            await ctx.db.execute(select(Project).where(Project.id == project_id, Project.user_id == ctx.user_id))
        ).scalar_one_or_none()
        if project is None:
            return f"Projekt '{project_id}' nicht gefunden."

    task = Task(
        user_id=ctx.user_id,
        project_id=project_id,
        title=title,
        description=arguments.get("description"),
        priority=arguments.get("priority", "medium"),
    )
    ctx.db.add(task)
    await ctx.db.commit()
    await ctx.db.refresh(task)
    return f"Aufgabe '{title}' angelegt (id={task.id})."


async def _prioritize_projects(arguments: dict, ctx: ToolContext) -> str:
    result = await ctx.db.execute(
        select(Project).where(Project.user_id == ctx.user_id, Project.status == "active")
    )
    projects = result.scalars().all()
    if not projects:
        return "Keine aktiven Projekte vorhanden."
    lines = [f"- {p.name}" + (f": {p.description}" if p.description else "") for p in projects]
    return "Aktive Projekte:\n" + "\n".join(lines)


register(
    Tool(
        name="create_task",
        description="Legt eine neue Aufgabe fuer den Nutzer an, optional einem Projekt zugeordnet.",
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "project_id": {"type": "string", "description": "UUID eines bestehenden Projekts (optional)"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]},
            },
            "required": ["title"],
        },
        handler=_create_task,
    )
)

register(
    Tool(
        name="prioritize_projects",
        description="Listet die aktiven Projekte des Nutzers auf, als Grundlage fuer Priorisierung.",
        input_schema={"type": "object", "properties": {}},
        handler=_prioritize_projects,
    )
)
