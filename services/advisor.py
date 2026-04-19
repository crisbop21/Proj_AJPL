"""Advisor service — generates coaching insights and recommended-therapist suggestions."""

import json
import re
import streamlit as st
import anthropic


ADVISOR_SYSTEM_PROMPT = """Eres un asistente experto para una coach de vida. Recibirás los resúmenes de las sesiones de un cliente y debes ayudar a la coach a reflexionar sobre el caso.

Devuelve ÚNICAMENTE un objeto JSON válido con estas claves exactas:
  patrones_observados (array of strings): 3-5 patrones, creencias o dinámicas recurrentes que notas en las sesiones.
  enfoques_sugeridos (array of strings): 3-5 enfoques, técnicas o preguntas poderosas que la coach podría probar en próximas sesiones. Concretas y accionables.
  ejercicios_recomendados (array of strings): 2-4 ejercicios o prácticas específicas (journaling, visualizaciones, experimentos conductuales, etc.) adecuadas para este cliente.
  senales_de_alerta (array of strings): 0-3 señales que podrían sugerir derivar a un profesional de salud mental (psicólogo o psiquiatra). Si no hay, devuelve [].
  referentes_recomendados (array of objects): 3-5 terapeutas, coaches o autores reconocidos y reputables cuyo trabajo se alinea con los temas del cliente. Cada objeto con las claves:
    nombre (string)
    enfoque (string): corriente o especialidad en pocas palabras
    por_que (string): por qué su trabajo es relevante para este cliente, 1-2 oraciones
    recurso_sugerido (string): libro, charla o concepto concreto para investigar

Solo incluye referentes reales, conocidos y con buena reputación profesional (ej: Brené Brown, Tara Brach, Viktor Frankl, Carl Rogers, Gabor Maté, Martha Beck, Byron Katie, Esther Perel, Pema Chödrön, Bessel van der Kolk, etc.). No inventes nombres.

Todo el contenido en español. Sin texto fuera del JSON. Sin bloques de código."""


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(1).strip()
    return json.loads(cleaned)


def _sessions_to_context(sessions: list[dict]) -> str:
    text = ""
    for s in sessions:
        summary = s.get("structured_summary", {})
        if isinstance(summary, str):
            try:
                summary = json.loads(summary)
            except Exception:
                summary = {}
        text += f"Sesión {s.get('session_number', '?')} ({s.get('recorded_at', '')[:10]}):\n"
        text += f"  Resumen: {summary.get('resumen_sesion', '')}\n"
        text += f"  Estado emocional: {summary.get('estado_emocional', '')}\n"
        for key, label in [
            ("objetivos_trabajados", "Objetivos"),
            ("obstaculos_identificados", "Obstáculos"),
            ("avances_y_revelaciones", "Avances"),
            ("compromisos_del_cliente", "Compromisos"),
            ("temas_pendientes", "Temas pendientes"),
        ]:
            items = summary.get(key, [])
            if items:
                text += f"  {label}: {', '.join(items)}\n"
        text += "\n"
    return text or "(sin sesiones)"


def generate_advice(client_name: str, sessions: list[dict], focus: str = "") -> dict:
    """Genera consejos y referentes para la coach basados en las sesiones del cliente."""
    context = _sessions_to_context(sessions)
    user_msg = f"Cliente: {client_name}\n\n{context}"
    if focus:
        user_msg += f"\n\nLa coach quiere enfocarse especialmente en: {focus}"

    try:
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            system=ADVISOR_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        return _extract_json(response.content[0].text)
    except Exception:
        st.error("Error al generar los consejos. Por favor intenta de nuevo.")
        return {
            "patrones_observados": [],
            "enfoques_sugeridos": [],
            "ejercicios_recomendados": [],
            "senales_de_alerta": [],
            "referentes_recomendados": [],
        }
