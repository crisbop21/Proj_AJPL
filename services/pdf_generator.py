import io
import json
import streamlit as st
import anthropic
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from xml.sax.saxutils import escape


def _register_fonts() -> str:
    """Register a font that supports Spanish characters. Returns the font name to use."""
    # Try to register DejaVu Sans which supports full Latin character set
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ]
    for path in font_paths:
        try:
            pdfmetrics.registerFont(TTFont("DejaVuSans", path))
            return "DejaVuSans"
        except Exception:
            continue
    # Fallback to Helvetica (built-in, limited accent support but works for most Spanish)
    return "Helvetica"


def _generate_resumen_general(sessions: list[dict]) -> str:
    """Genera un resumen general de todas las sesiones usando Claude."""
    summaries_text = ""
    for s in sessions:
        summary = s.get("structured_summary", {})
        if isinstance(summary, str):
            summary = json.loads(summary)
        summaries_text += f"Sesion {s.get('session_number', '?')}:\n"
        summaries_text += f"  Resumen: {summary.get('resumen_sesion', '')}\n"
        summaries_text += f"  Avances: {', '.join(summary.get('avances_y_revelaciones', []))}\n"
        summaries_text += f"  Compromisos: {', '.join(summary.get('compromisos_del_cliente', []))}\n\n"

    try:
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system="Eres un asistente para una coach de vida. Genera un resumen general breve (2-3 parrafos) del progreso del cliente basandote en todas sus sesiones. Todo en espanol.",
            messages=[{"role": "user", "content": summaries_text}],
        )
        return response.content[0].text
    except Exception:
        st.error("Error al generar el resumen general del PDF.")
        return "No se pudo generar el resumen general."


def _safe(text: str) -> str:
    """Escape text for safe use in ReportLab Paragraph XML."""
    return escape(str(text))


def generate_pdf(client_name: str, sessions: list[dict]) -> bytes:
    """Genera un reporte PDF con el historial de sesiones del cliente."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            topMargin=0.75 * inch, bottomMargin=0.75 * inch,
                            leftMargin=0.75 * inch, rightMargin=0.75 * inch)

    font_name = _register_fonts()

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontName=font_name,
                                  fontSize=20, spaceAfter=20)
    heading_style = ParagraphStyle("Heading", parent=styles["Heading2"], fontName=font_name,
                                    fontSize=14, spaceAfter=10)
    body_style = ParagraphStyle("Body2", parent=styles["Normal"], fontName=font_name,
                                 fontSize=11, leading=15)
    bullet_style = ParagraphStyle("Bullet", parent=body_style, leftIndent=20, bulletIndent=10)

    story = []

    # --- Cover page ---
    dates = [s.get("recorded_at", "")[:10] for s in sessions if s.get("recorded_at")]
    date_range = f"{min(dates)} — {max(dates)}" if dates else "Sin fechas"

    story.append(Paragraph(_safe("Reporte de Coaching"), title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Cliente:</b> {_safe(client_name)}", body_style))
    story.append(Paragraph(f"<b>Periodo:</b> {_safe(date_range)}", body_style))
    story.append(Paragraph(f"<b>Total de sesiones:</b> {len(sessions)}", body_style))
    story.append(Spacer(1, 20))

    # Resumen general
    story.append(Paragraph("Resumen General", heading_style))
    resumen_general = _generate_resumen_general(sessions)
    for paragraph in resumen_general.split("\n"):
        if paragraph.strip():
            story.append(Paragraph(_safe(paragraph.strip()), body_style))
            story.append(Spacer(1, 6))

    story.append(PageBreak())

    # --- Session history ---
    story.append(Paragraph("Historial de Sesiones", title_style))
    story.append(Spacer(1, 12))

    for s in sessions:
        summary = s.get("structured_summary", {})
        if isinstance(summary, str):
            summary = json.loads(summary)

        session_date = s.get("recorded_at", "")[:10]
        session_num = s.get("session_number", "?")

        story.append(Paragraph(f"Sesion {session_num} — {_safe(session_date)}", heading_style))

        # Resumen
        resumen = summary.get("resumen_sesion", "")
        if resumen:
            story.append(Paragraph(f"<b>Resumen:</b> {_safe(resumen)}", body_style))
            story.append(Spacer(1, 6))

        # Compromisos
        compromisos = summary.get("compromisos_del_cliente", [])
        if compromisos:
            story.append(Paragraph("<b>Compromisos del Cliente:</b>", body_style))
            for item in compromisos:
                story.append(Paragraph(f"• {_safe(item)}", bullet_style))
            story.append(Spacer(1, 6))

        # Avances
        avances = summary.get("avances_y_revelaciones", [])
        if avances:
            story.append(Paragraph("<b>Avances y Revelaciones:</b>", body_style))
            for item in avances:
                story.append(Paragraph(f"• {_safe(item)}", bullet_style))
            story.append(Spacer(1, 6))

        story.append(Spacer(1, 16))

    story.append(PageBreak())

    # --- Temas pendientes ---
    story.append(Paragraph("Temas Pendientes", title_style))
    story.append(Spacer(1, 12))

    all_temas = set()
    for s in sessions:
        summary = s.get("structured_summary", {})
        if isinstance(summary, str):
            summary = json.loads(summary)
        for tema in summary.get("temas_pendientes", []):
            all_temas.add(tema)

    if all_temas:
        for tema in sorted(all_temas):
            story.append(Paragraph(f"• {_safe(tema)}", bullet_style))
    else:
        story.append(Paragraph("No hay temas pendientes registrados.", body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
