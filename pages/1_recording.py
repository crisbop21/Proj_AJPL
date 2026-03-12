import tempfile
import os
import streamlit as st
from pydub import AudioSegment
from io import BytesIO
from services.database import get_all_clients, save_session
from services.transcription import transcribe_audio
from services.structuring import structure_notes

st.title("Nueva Sesión")

# --- Seleccionar cliente ---
clients = get_all_clients()
if not clients:
    st.warning("No hay clientes registrados. Agrega uno en la página de Clientes.")
    st.stop()

client_options = {c["name"]: c["id"] for c in clients}
selected_name = st.selectbox("Seleccionar cliente", list(client_options.keys()))
selected_client_id = client_options[selected_name]

# --- Grabar audio ---
st.subheader("Grabar nota de voz")
audio_data = st.audio_input("Pulsa para grabar tu nota de voz")

if audio_data is not None:
    if st.button("Transcribir y estructurar"):
        # Export audio to temp WAV file
        tmp_path = None
        try:
            with st.spinner("Exportando audio..."):
                audio_segment = AudioSegment.from_file(BytesIO(audio_data.read()))
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp_path = tmp.name
                    audio_segment.export(tmp.name, format="wav")

            # Transcribe
            with st.spinner("Transcribiendo audio..."):
                transcript = transcribe_audio(tmp_path)
        except Exception:
            st.error("Error al transcribir el audio. Por favor intenta de nuevo.")
            st.stop()
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

        # Store transcript in session state so it persists
        st.session_state["current_transcript"] = transcript

    # Show editable transcript if available
    if "current_transcript" in st.session_state:
        st.subheader("Transcripción")
        edited_transcript = st.text_area(
            "Puedes editar la transcripción antes de estructurar:",
            value=st.session_state["current_transcript"],
            height=200,
        )

        # Structure notes if not already done
        if "pending_summary" not in st.session_state:
            with st.spinner("Estructurando notas con IA..."):
                try:
                    summary = structure_notes(edited_transcript)
                except Exception:
                    st.error("Error al estructurar las notas. Por favor intenta de nuevo.")
                    st.stop()
            st.session_state["pending_summary"] = summary
            st.session_state["pending_transcript"] = edited_transcript
            st.session_state["pending_client_id"] = selected_client_id

        summary = st.session_state["pending_summary"]

        # Display structured summary
        st.subheader("Resumen Estructurado")
        field_labels = {
            "resumen_sesion": "Resumen de la Sesión",
            "objetivos_trabajados": "Objetivos Trabajados",
            "obstaculos_identificados": "Obstáculos Identificados",
            "avances_y_revelaciones": "Avances y Revelaciones",
            "compromisos_del_cliente": "Compromisos del Cliente",
            "temas_pendientes": "Temas Pendientes",
            "estado_emocional": "Estado Emocional",
        }

        for key, label in field_labels.items():
            with st.expander(label, expanded=True):
                value = summary.get(key, "")
                if isinstance(value, list):
                    for item in value:
                        st.markdown(f"- {item}")
                else:
                    st.write(value)

        # Save button
        if st.button("Guardar sesión"):
            try:
                with st.spinner("Guardando sesión..."):
                    save_session(
                        st.session_state["pending_client_id"],
                        st.session_state["pending_transcript"],
                        st.session_state["pending_summary"],
                    )
                st.success("Sesión guardada correctamente.")
                del st.session_state["current_transcript"]
                del st.session_state["pending_transcript"]
                del st.session_state["pending_summary"]
                del st.session_state["pending_client_id"]
            except Exception:
                pass  # Error already shown by save_session
