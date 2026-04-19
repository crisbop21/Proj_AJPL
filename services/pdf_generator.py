import io
import json
import re
import streamlit as st
import anthropic
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from xml.sax.saxutils import escape


REPORT_SECTIONS_SYSTEM_PROMPT = """Eres un asistente para una coach de vida. Recibirás los resúmenes estructurados de todas las sesiones de un cliente y debes producir un reporte sintético.

Devuelve ÚNICAMENTE un objeto JSON válido con estas claves exactas:
  motivo_consulta (string): razón por la que el cliente acudió a coaching, inferida del primer resumen o del conjunto. Breve, 1-3 oraciones. Si no queda claro, usa "Por definir".
  resumen_temas_trabajados (string): párrafo descriptivo de los temas principales que se trabajaron a lo largo de las sesiones.
  avances (string): párrafo describiendo los avances y revelaciones más significativos del cliente.
  compromisos_y_recomendaciones (string): párrafo con los compromisos asumidos por el cliente y recomendaciones de la coach.

Todo el contenido en español. Sin texto fuera del JSON. Sin bloques de código."""


def _register_fonts() -> str:
    """Register a font that supports Spanish characters. Returns the font name to use."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ]
    for path in font_paths:
        try:
            pdfmetrics.registerFont(TTFont("DejaVuSans", path))
            try:
                pdfmetrics.registerFont(TTFont("DejaVuSans-Bold",
                                               path.replace("DejaVuSans.ttf", "DejaVuSans-Bold.ttf")))
            except Exception:
                pass
            return "DejaVuSans"
        except Exception:
            continue
    return "Helvetica"


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(1).strip()
    return json.loads(cleaned)


def _summaries_to_text(sessions: list[dict]) -> str:
    summaries_text = ""
    for s in sessions:
        summary = s.get("structured_summary", {})
        if isinstance(summary, str):
            try:
                summary = json.loads(summary)
            except Exception:
                summary = {}
        summaries_text += f"Sesión {s.get('session_number', '?')} ({s.get('recorded_at', '')[:10]}):\n"
        summaries_text += f"  Resumen: {summary.get('resumen_sesion', '')}\n"
        objetivos = summary.get("objetivos_trabajados", [])
        if objetivos:
            summaries_text += f"  Objetivos: {', '.join(objetivos)}\n"
        avances = summary.get("avances_y_revelaciones", [])
        if avances:
            summaries_text += f"  Avances: {', '.join(avances)}\n"
        compromisos = summary.get("compromisos_del_cliente", [])
        if compromisos:
            summaries_text += f"  Compromisos: {', '.join(compromisos)}\n"
        obstaculos = summary.get("obstaculos_identificados", [])
        if obstaculos:
            summaries_text += f"  Obstáculos: {', '.join(obstaculos)}\n"
        summaries_text += "\n"
    return summaries_text


def generate_report_sections(sessions: list[dict], feedback: str = "") -> dict:
    """Genera las secciones del reporte (motivo, temas, avances, compromisos) usando Claude."""
    summaries_text = _summaries_to_text(sessions)

    system_prompt = REPORT_SECTIONS_SYSTEM_PROMPT
    if feedback:
        system_prompt += (
            "\n\nLa coach ha dado el siguiente feedback sobre la versión anterior. "
            f"Ajusta las secciones según estas indicaciones:\n{feedback}"
        )

    try:
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": summaries_text or "(sin sesiones)"}],
        )
        return _extract_json(response.content[0].text)
    except Exception:
        st.error("Error al generar las secciones del reporte.")
        return {
            "motivo_consulta": "",
            "resumen_temas_trabajados": "",
            "avances": "",
            "compromisos_y_recomendaciones": "",
        }


def _safe(text: str) -> str:
    return escape(str(text or ""))


def _paragraphs(text: str, style) -> list:
    """Split text by newlines and produce one Paragraph per non-empty block."""
    items = []
    for block in (text or "").split("\n"):
        block = block.strip()
        if block:
            items.append(Paragraph(_safe(block), style))
            items.append(Spacer(1, 6))
    return items


def generate_pdf(
    client_name: str,
    sessions: list[dict],
    documento_identidad: str = "",
    motivo_consulta: str = "",
    resumen_temas_trabajados: str = "",
    avances: str = "",
    compromisos_y_recomendaciones: str = "",
    firma: str = "",
) -> bytes:
    """Genera un reporte PDF con la estructura solicitada por la coach."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
    )

    font_name = _register_fonts()
    bold_font = "DejaVuSans-Bold" if font_name == "DejaVuSans" else "Helvetica-Bold"

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title2", parent=styles["Title"], fontName=bold_font, fontSize=20, spaceAfter=18,
    )
    heading_style = ParagraphStyle(
        "Heading", parent=styles["Heading2"], fontName=bold_font,
        fontSize=13, spaceBefore=10, spaceAfter=6, textColor="#5a3fc7",
    )
    body_style = ParagraphStyle(
        "Body2", parent=styles["Normal"], fontName=font_name, fontSize=11, leading=15,
    )
    meta_style = ParagraphStyle(
        "Meta", parent=body_style, fontSize=11, leading=15, spaceAfter=4,
    )
    signature_style = ParagraphStyle(
        "Signature", parent=body_style, alignment=1, fontSize=11, leading=14,
    )

    story = []

    # --- Title ---
    story.append(Paragraph("Reporte de Coaching", title_style))
    story.append(Spacer(1, 4))

    # --- Cliente + documento ---
    doc_label = documento_identidad.strip() or "—"
    story.append(Paragraph(
        f"<b>Cliente:</b> {_safe(client_name)} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Documento de identidad:</b> {_safe(doc_label)}",
        meta_style,
    ))

    # --- Motivo de consulta ---
    story.append(Paragraph("Motivo de consulta", heading_style))
    story.extend(_paragraphs(motivo_consulta or "—", body_style))

    # --- Número de sesiones + fecha última ---
    dates = sorted([s.get("recorded_at", "")[:10] for s in sessions if s.get("recorded_at")])
    last_date = dates[-1] if dates else "—"
    story.append(Paragraph("Sesiones", heading_style))
    story.append(Paragraph(
        f"<b>Número de sesiones:</b> {len(sessions)} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Fecha de la última sesión:</b> {_safe(last_date)}",
        meta_style,
    ))
    story.append(Spacer(1, 6))

    # --- Resumen de temas trabajados ---
    story.append(Paragraph("Resumen de temas trabajados", heading_style))
    story.extend(_paragraphs(resumen_temas_trabajados or "—", body_style))

    # --- Avances ---
    story.append(Paragraph("Avances", heading_style))
    story.extend(_paragraphs(avances or "—", body_style))

    # --- Compromisos y recomendaciones ---
    story.append(Paragraph("Compromisos y recomendaciones", heading_style))
    story.extend(_paragraphs(compromisos_y_recomendaciones or "—", body_style))

    # --- Firma ---
    story.append(Spacer(1, 40))
    story.append(Paragraph("_" * 40, signature_style))
    story.append(Paragraph(_safe(firma.strip() or "Firma"), signature_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
