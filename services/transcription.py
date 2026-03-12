import streamlit as st
from elevenlabs import ElevenLabs


def transcribe_audio(audio_path: str) -> str:
    """Transcribe un archivo de audio WAV a texto usando ElevenLabs Scribe v2."""
    try:
        client = ElevenLabs(api_key=st.secrets["ELEVENLABS_API_KEY"])
        with open(audio_path, "rb") as f:
            result = client.speech_to_text.convert(
                file=f,
                model_id="scribe_v2",
                language_code="es",
            )
        return result.text
    except Exception as e:
        st.error("Error al transcribir el audio. Por favor intenta de nuevo.")
        raise
