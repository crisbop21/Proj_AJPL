import tempfile
import os
import streamlit as st
from pydub import AudioSegment
from io import BytesIO
from services.auth import check_password
from services.database import (
    get_all_clients,
    save_session,
    update_session,
    get_sessions_for_client,
)
from services.transcription import transcribe_audio
from services.structuring import structure_notes
from services.styles import inject_custom_css, render_sidebar_brand, step_indicator, page_header

inject_custom_css()
render_sidebar_brand()
check_password()

page_header("🎤 Nueva Sesión", "Graba, transcribe y estructura tus notas de coaching")

# --- Seleccionar cliente ---
clients = get_all_clients()
if not clients:
    st.warning("No hay clientes registrados. Agrega uno en la página de **Clientes**.")
    st.stop()

client_options = {c["name"]: c["id"] for c in clients}

# Track workflow state
has_transcript = "current_transcript" in st.session_state
has_summary = "pending_summary" in st.session_state

# --- Mode selector: new session vs. append to existing ---
mode = st.radio(
    "¿Qué deseas hacer?",
    ["Nueva sesión", "Añadir a sesión existente"],
    horizontal=True,
    key="recording_mode",
)
is_append_mode = mode == "Añadir a sesión existente"

# Clear pending state if mode changes
if st.session_state.get("_last_mode") != mode:
    for key in [
        "current_transcript",
        "pending_transcript",
        "pending_summary",
        "pending_client_id",
        "pending_session_id",
        "pending_existing_transcript",
    ]:
        st.session_state.pop(key, None)
    st.session_state["_last_mode"] = mode
    has_transcript = False
    has_summary = False

# --- Step 1: Client selection ---
step_indicator(1, "Seleccionar cliente", done=has_transcript)
selected_name = st.selectbox(
    "Cliente",
    list(client_options.keys()),
    label_visibility="collapsed",
    placeholder="Elige un cliente...",
)
selected_client_id = client_options[selected_name]

# --- Step 1b (append mode): Select existing session ---
selected_session = None
if is_append_mode:
    st.markdown("")
    step_indicator(2, "Seleccionar sesión existente", done=has_transcript)
    existing_sessions = get_sessions_for_client(selected_client_id)
    if not existing_sessions:
        st.info("Este cliente no tiene sesiones registradas. Cambia a **Nueva sesión** para crear la primera.")
        st.stop()

    session_labels = {
        f"Sesión {s.get('session_number', '?')} — {s.get('recorded_at', '')[:10]}": s
        for s in existing_sessions
    }
    selected_label = st.selectbox(
        "Sesión",
        list(session_labels.keys()),
        label_visibility="collapsed",
        placeholder="Elige una sesión...",
    )
    selected_session = session_labels[selected_label]

    with st.expander("Ver transcripción actual de la sesión", expanded=False):
        st.text(selected_session.get("raw_transcript", "") or "(vacía)")

st.markdown("")

# --- Record audio step ---
record_step_num = 3 if is_append_mode else 2
record_label = "Grabar nota adicional" if is_append_mode else "Grabar nota de voz"
step_indicator(record_step_num, record_label, done=has_transcript)
audio_data = st.audio_input("Pulsa para grabar tu nota de voz")

if audio_data is not None:
    button_label = (
        "Transcribir y añadir a la sesión" if is_append_mode else "Transcribir y estructurar"
    )
    if st.button(button_label, type="primary", use_container_width=True):
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
                new_transcript = transcribe_audio(tmp_path)
        except Exception:
            st.error("Error al transcribir el audio. Por favor intenta de nuevo.")
            st.stop()
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

        # Validate transcript is not empty or meaningless
        cleaned = new_transcript.strip().strip("[]").strip()
        if not cleaned or cleaned.lower() in ("silencio", "silence", "..."):
            st.warning("La transcripción está vacía o solo contiene silencio. Graba una nota de voz más larga.")
            st.stop()

        # In append mode, concatenate with existing transcript
        if is_append_mode and selected_session is not None:
            existing_text = (selected_session.get("raw_transcript") or "").strip()
            combined = (
                f"{existing_text}\n\n[Adición]\n{new_transcript}"
                if existing_text
                else new_transcript
            )
            st.session_state["current_transcript"] = combined
            st.session_state["pending_session_id"] = selected_session["id"]
            st.session_state["pending_existing_transcript"] = existing_text
        else:
            st.session_state["current_transcript"] = new_transcript
            st.session_state.pop("pending_session_id", None)
            st.session_state.pop("pending_existing_transcript", None)

# Show editable transcript if available
if "current_transcript" in st.session_state:
    review_step_num = 4 if is_append_mode else 3
    summary_step_num = 5 if is_append_mode else 4

    st.markdown("")
    step_indicator(review_step_num, "Revisar transcripción", done=has_summary)

    edited_transcript = st.text_area(
        "Puedes editar la transcripción antes de guardar:",
        value=st.session_state["current_transcript"],
        height=220 if is_append_mode else 180,
    )

    # Structure notes if not already done
    if "pending_summary" not in st.session_state:
        with st.spinner("Estructurando notas con IA..."):
            try:
                summary = structure_notes(edited_transcript)
            except Exception:
                st.stop()
        st.session_state["pending_summary"] = summary
        st.session_state["pending_transcript"] = edited_transcript
        st.session_state["pending_client_id"] = selected_client_id

    summary = st.session_state["pending_summary"]

    # --- Structured summary ---
    st.markdown("")
    step_indicator(summary_step_num, "Resumen estructurado", done=False)

    # Display summary fields in a cleaner layout
    _field_icons = {
        "resumen_sesion": "📝",
        "objetivos_trabajados": "🎯",
        "obstaculos_identificados": "🚧",
        "avances_y_revelaciones": "💡",
        "compromisos_del_cliente": "🤝",
        "temas_pendientes": "📌",
        "estado_emocional": "💭",
    }
    _field_labels = {
        "resumen_sesion": "Resumen de la Sesión",
        "objetivos_trabajados": "Objetivos Trabajados",
        "obstaculos_identificados": "Obstáculos Identificados",
        "avances_y_revelaciones": "Avances y Revelaciones",
        "compromisos_del_cliente": "Compromisos del Cliente",
        "temas_pendientes": "Temas Pendientes",
        "estado_emocional": "Estado Emocional",
    }

    # Show estado_emocional as a badge at the top
    estado = summary.get("estado_emocional", "")
    if estado:
        st.markdown(
            f'<span class="field-tag">💭 Estado Emocional</span> '
            f'<span class="emotion-badge">{estado}</span>',
            unsafe_allow_html=True,
        )
        st.markdown("")

    # Resumen as a highlighted card
    resumen = summary.get("resumen_sesion", "")
    if resumen:
        st.markdown(
            f"""<div class="ui-card">
                <span class="field-tag">📝 Resumen de la Sesión</span>
                <p style="margin:0.5rem 0 0 0; color:#333;">{resumen}</p>
            </div>""",
            unsafe_allow_html=True,
        )

    # Remaining list fields in two columns
    list_fields = [
        ("objetivos_trabajados", "🎯", "Objetivos Trabajados"),
        ("obstaculos_identificados", "🚧", "Obstáculos Identificados"),
        ("avances_y_revelaciones", "💡", "Avances y Revelaciones"),
        ("compromisos_del_cliente", "🤝", "Compromisos del Cliente"),
        ("temas_pendientes", "📌", "Temas Pendientes"),
    ]

    col_left, col_right = st.columns(2)
    for i, (key, icon, label) in enumerate(list_fields):
        value = summary.get(key, [])
        if not value:
            continue
        target_col = col_left if i % 2 == 0 else col_right
        with target_col:
            with st.expander(f"{icon} {label}", expanded=True):
                for item in value:
                    st.markdown(f"- {item}")

    # Save button
    st.markdown("")
    st.divider()

    is_updating_existing = (
        is_append_mode and st.session_state.get("pending_session_id") is not None
    )
    save_label = (
        "💾 Actualizar sesión" if is_updating_existing else "💾 Guardar sesión"
    )

    col_save, col_cancel = st.columns([3, 1])
    with col_save:
        if st.button(save_label, type="primary", use_container_width=True):
            try:
                if is_updating_existing:
                    with st.spinner("Actualizando sesión..."):
                        update_session(
                            st.session_state["pending_session_id"],
                            st.session_state["pending_transcript"],
                            st.session_state["pending_summary"],
                        )
                    st.success("Sesión actualizada correctamente.")
                else:
                    with st.spinner("Guardando sesión..."):
                        save_session(
                            st.session_state["pending_client_id"],
                            st.session_state["pending_transcript"],
                            st.session_state["pending_summary"],
                        )
                    st.success("Sesión guardada correctamente.")
                for key in [
                    "current_transcript",
                    "pending_transcript",
                    "pending_summary",
                    "pending_client_id",
                    "pending_session_id",
                    "pending_existing_transcript",
                ]:
                    st.session_state.pop(key, None)
            except Exception:
                pass  # Error already shown by save_session/update_session
    with col_cancel:
        if st.button("Descartar", use_container_width=True):
            for key in [
                "current_transcript",
                "pending_transcript",
                "pending_summary",
                "pending_client_id",
                "pending_session_id",
                "pending_existing_transcript",
            ]:
                st.session_state.pop(key, None)
            st.rerun()
