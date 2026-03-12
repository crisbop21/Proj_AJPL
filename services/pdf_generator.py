import io
import json
import streamlit as st
import anthropic
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak


def _generate_resumen_general(sessions: list[dict]) -> str:
    """Genera un resumen general de todas las sesiones usando Claude."""
    summaries_text = ""
    for s in sessions:
        summary = s.get("structured_summary", {})
        if isinstance(summary, str):
            summary = json.loads(summary)
        summaries_text += f"Sesión {s.get('session_number', '?')}:\n"
        summaries_text += f"  Resumen: {summary.get('resumen_sesion', '')}\n"
        summaries_text += f"  Avances: {', '.join(summary.get('avances_y_revelaciones', []))}\n"
        summaries_text += f"  Compromisos: {', '.join(summary.get('compromisos_del_cliente', []))}\n\n"

    try:
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system="Eres un asistente para una coach de vida. Genera un resumen general breve (2-3 párrafos) del progreso del cliente basándote en todas sus sesiones. Todo en español.",
            messages=[{"role": "user", "content": summaries_text}],
        )
        return response.content[0].text
    except Exception:
        return "No se pudo generar el resumen general."


def generate_pdf(client_name: str, sessions: list[dict]) -> bytes:
    """Genera un reporte PDF con el historial de sesiones del cliente."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            topMargin=0.75 * inch, bottomMargin=0.75 * inch,
                            leftMargin=0.75 * inch, rightMargin=0.75 * inch)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=20, spaceAfter=20)
    heading_style = ParagraphStyle("Heading", parent=styles["Heading2"], fontSize=14, spaceAfter=10)
    body_style = ParagraphStyle("Body2", parent=styles["Normal"], fontSize=11, leading=15)
    bullet_style = ParagraphStyle("Bullet", parent=body_style, leftIndent=20, bulletIndent=10)

    story = []

    # --- Cover page ---
    dates = [s.get("recorded_at", "")[:10] for s in sessions if s.get("recorded_at")]
    date_range = f"{min(dates)} — {max(dates)}" if dates else "Sin fechas"

    story.append(Paragraph(f"Reporte de Coaching", title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Cliente:</b> {client_name}", body_style))
    story.append(Paragraph(f"<b>Período:</b> {date_range}", body_style))
    story.append(Paragraph(f"<b>Total de sesiones:</b> {len(sessions)}", body_style))
    story.append(Spacer(1, 20))

    # Resumen general
    story.append(Paragraph("Resumen General", heading_style))
    with st.spinner("Generando resumen general para el PDF..."):
        resumen_general = _generate_resumen_general(sessions)
    for paragraph in resumen_general.split("\n"):
        if paragraph.strip():
            story.append(Paragraph(paragraph.strip(), body_style))
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

        story.append(Paragraph(f"Sesión {session_num} — {session_date}", heading_style))

        # Resumen
        resumen = summary.get("resumen_sesion", "")
        if resumen:
            story.append(Paragraph(f"<b>Resumen:</b> {resumen}", body_style))
            story.append(Spacer(1, 6))

        # Compromisos
        compromisos = summary.get("compromisos_del_cliente", [])
        if compromisos:
            story.append(Paragraph("<b>Compromisos del Cliente:</b>", body_style))
            for item in compromisos:
                story.append(Paragraph(f"• {item}", bullet_style))
            story.append(Spacer(1, 6))

        # Avances
        avances = summary.get("avances_y_revelaciones", [])
        if avances:
            story.append(Paragraph("<b>Avances y Revelaciones:</b>", body_style))
            for item in avances:
                story.append(Paragraph(f"• {item}", bullet_style))
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
            story.append(Paragraph(f"• {tema}", bullet_style))
    else:
        story.append(Paragraph("No hay temas pendientes registrados.", body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
