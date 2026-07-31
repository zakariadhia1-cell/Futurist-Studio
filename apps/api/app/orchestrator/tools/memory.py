from app.memory.search import search_documents, search_memory_facts
from app.orchestrator.tool_registry import Tool, ToolContext, register


async def _read_memory(arguments: dict, ctx: ToolContext) -> str:
    query = str(arguments.get("query", "")).strip()
    if not query:
        return "Kein Suchbegriff angegeben."

    chunks = await search_documents(ctx.db, ctx.user_id, query, top_k=5)
    facts = await search_memory_facts(ctx.db, ctx.user_id, query, top_k=5)
    if not chunks and not facts:
        return "Nichts Relevantes im Gedaechtnis gefunden."

    lines = []
    for fact in facts:
        lines.append(f"[Fakt] {fact.subject}: {fact.fact_text} (Distanz {fact.distance:.3f})")
    for chunk in chunks:
        lines.append(f"[Aus '{chunk.document_title}'] {chunk.content} (Distanz {chunk.distance:.3f})")
    return "\n".join(lines)


register(
    Tool(
        name="read_memory",
        description=(
            "Durchsucht die Wissensdatenbank (Dokumente und gespeicherte Fakten) des Nutzers nach "
            "einem Suchbegriff und gibt die relevantesten Treffer zurueck."
        ),
        input_schema={
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Wonach gesucht werden soll"}},
            "required": ["query"],
        },
        handler=_read_memory,
    )
)
