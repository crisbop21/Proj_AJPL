import json
import streamlit as st
import anthropic

SYSTEM_PROMPT = """Eres un asistente para una coach de vida. Recibirás la transcripción
de una nota de voz en español grabada tras una sesión con un cliente.

Devuelve ÚNICAMENTE un objeto JSON válido con estas claves exactas:
  resumen_sesion (string)
  objetivos_trabajados (array of strings)
  obstaculos_identificados (array of strings)
  avances_y_revelaciones (array of strings)
  compromisos_del_cliente (array of strings)
  temas_pendientes (array of strings)
  estado_emocional (string)

Sin texto fuera del JSON. Sin bloques de código. Solo el objeto JSON. Todo en español."""


def structure_notes(transcript: str) -> dict:
    """Estructura la transcripción en los 7 campos de coaching usando Claude."""
    try:
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": transcript}],
        )
        text = response.content[0].text
        return json.loads(text)
    except json.JSONDecodeError:
        # Retry asking Claude to fix the JSON
        try:
            retry_response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                system="Devuelve ÚNICAMENTE un objeto JSON válido. Sin texto adicional.",
                messages=[
                    {"role": "user", "content": f"Corrige este JSON:\n{text}"},
                ],
            )
            return json.loads(retry_response.content[0].text)
        except Exception as retry_err:
            st.error(f"Error al procesar la respuesta de Claude: {retry_err}")
            raise
    except Exception as e:
        st.error(f"Error al estructurar las notas: {e}")
        raise
