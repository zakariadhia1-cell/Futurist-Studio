"""Finance Agent: safe arithmetic, invoice and report PDF generation."""
import os
import uuid
from datetime import date
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.orchestrator.tool_registry import Tool, ToolContext, register
from app.orchestrator.tools.calculator import safe_eval
from app.orchestrator.tools.sandbox import user_workspace_dir


async def _calculate(arguments: dict, ctx: ToolContext) -> str:
    expression = str(arguments.get("expression", "")).strip()
    if not expression:
        return "Kein Ausdruck angegeben."
    try:
        result = safe_eval(expression)
    except (ValueError, ZeroDivisionError, SyntaxError, TypeError) as exc:
        return f"Konnte nicht berechnet werden: {exc}"
    return f"{expression} = {result}"


def _build_invoice_pdf(path: str, client_name: str, items: list[dict], invoice_number: str, notes: str) -> float:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(path, pagesize=A4)
    story = [
        Paragraph(f"Rechnung {escape(invoice_number)}", styles["Title"]),
        Paragraph(f"An: {escape(client_name)}", styles["Normal"]),
        Paragraph(f"Datum: {date.today().isoformat()}", styles["Normal"]),
        Spacer(1, 1 * cm),
    ]

    table_data = [["Beschreibung", "Menge", "Einzelpreis", "Summe"]]
    total = 0.0
    for item in items:
        qty = float(item.get("quantity", 1))
        price = float(item.get("unit_price", 0))
        line_total = qty * price
        total += line_total
        table_data.append(
            [str(item.get("description", "")), f"{qty:g}", f"{price:.2f} EUR", f"{line_total:.2f} EUR"]
        )
    table_data.append(["", "", "Gesamt", f"{total:.2f} EUR"])

    table = Table(table_data, colWidths=[8 * cm, 2 * cm, 3 * cm, 3 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1b1e23")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ]
        )
    )
    story.append(table)

    if notes:
        story.append(Spacer(1, 1 * cm))
        story.append(Paragraph(escape(notes), styles["Normal"]))

    doc.build(story)
    return total


async def _generate_invoice_pdf(arguments: dict, ctx: ToolContext) -> str:
    client_name = str(arguments.get("client_name", "")).strip()
    items = arguments.get("items") or []
    if not client_name or not items:
        return "client_name und items (Liste von {description, quantity, unit_price}) sind erforderlich."

    invoice_number = str(arguments.get("invoice_number") or f"RE-{uuid.uuid4().hex[:8].upper()}")
    notes = str(arguments.get("notes", ""))

    workspace = user_workspace_dir(ctx.user_id)
    invoices_dir = os.path.join(workspace, "invoices")
    os.makedirs(invoices_dir, exist_ok=True)
    filename = f"{invoice_number}.pdf"
    path = os.path.join(invoices_dir, filename)

    try:
        total = _build_invoice_pdf(path, client_name, items, invoice_number, notes)
    except Exception as exc:
        return f"Rechnung konnte nicht erstellt werden: {exc}"

    return f"Rechnung {invoice_number} erstellt: invoices/{filename} (Gesamt: {total:.2f} EUR)."


def _build_report_pdf(path: str, title: str, content: str) -> None:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(path, pagesize=A4)
    story = [Paragraph(escape(title), styles["Title"]), Spacer(1, 0.5 * cm)]
    for paragraph in content.split("\n\n"):
        if paragraph.strip():
            story.append(Paragraph(escape(paragraph).replace("\n", "<br/>"), styles["Normal"]))
            story.append(Spacer(1, 0.3 * cm))
    doc.build(story)


async def _generate_report(arguments: dict, ctx: ToolContext) -> str:
    title = str(arguments.get("title", "")).strip()
    content = str(arguments.get("content", "")).strip()
    if not title or not content:
        return "title und content sind erforderlich."

    workspace = user_workspace_dir(ctx.user_id)
    reports_dir = os.path.join(workspace, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex[:8]}.pdf"
    path = os.path.join(reports_dir, filename)

    try:
        _build_report_pdf(path, title, content)
    except Exception as exc:
        return f"Bericht konnte nicht erstellt werden: {exc}"

    return f"Bericht '{title}' erstellt: reports/{filename}."


register(
    Tool(
        name="calculate",
        description="Berechnet einen mathematischen Ausdruck (Grundrechenarten, Potenzen, Klammern).",
        input_schema={
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "z.B. '1200 * 1.19'"}},
            "required": ["expression"],
        },
        handler=_calculate,
    )
)

register(
    Tool(
        name="generate_invoice_pdf",
        description="Erstellt eine PDF-Rechnung mit Positionen und speichert sie im Workspace unter invoices/.",
        input_schema={
            "type": "object",
            "properties": {
                "client_name": {"type": "string"},
                "invoice_number": {"type": "string"},
                "notes": {"type": "string"},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "quantity": {"type": "number"},
                            "unit_price": {"type": "number"},
                        },
                        "required": ["description", "quantity", "unit_price"],
                    },
                },
            },
            "required": ["client_name", "items"],
        },
        handler=_generate_invoice_pdf,
    )
)

register(
    Tool(
        name="generate_report",
        description="Erstellt einen PDF-Bericht aus Titel und Text und speichert ihn im Workspace unter reports/.",
        input_schema={
            "type": "object",
            "properties": {"title": {"type": "string"}, "content": {"type": "string"}},
            "required": ["title", "content"],
        },
        handler=_generate_report,
    )
)
