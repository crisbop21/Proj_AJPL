import streamlit as st
from services.auth import check_password
from services.database import get_all_clients, get_sessions_for_client
from services.pdf_generator import generate_pdf, generate_resumen_general
from services.styles import inject_custom_css, render_sidebar_brand, page_header, metric_card

inject_custom_css()
render_sidebar_brand()
check_password()

page_header("📋 Historial", "Consulta sesiones anteriores y genera reportes")

# --- Seleccionar cliente ---
clients = get_all_clients()
if not clients:
    st.warning("No hay clientes registrados. Agrega uno en la página de **Clientes**.")
    st.stop()

client_options = {c["name"]: c["id"] for c in clients}
selected_name = st.selectbox(
    "Seleccionar cliente",
    list(client_options.keys()),
    label_visibility="collapsed",
    placeholder="Elige un cliente...",
)
selected_client_id = client_options[selected_name]

# --- Mostrar sesiones ---
sessions = get_sessions_for_client(selected_client_id)

if not sessions:
    st.markdown("")
    st.info("Este cliente no tiene sesiones registradas.")
    st.stop()

# --- Metrics row ---
st.markdown("")
total_sessions = len(sessions)
first_date = sessions[-1].get("recorded_at", "")[:10] if sessions else "—"
last_date = sessions[0].get("recorded_at", "")[:10] if sessions else "—"

col1, col2, col3 = st.columns(3)
with col1:
    metric_card(str(total_sessions), "Sesiones totales")
with col2:
    metric_card(first_date, "Primera sesión")
with col3:
    metric_card(last_date, "Última sesión")

st.markdown("")

# --- PDF generation with preview and feedback ---
col_pdf, col_spacer = st.columns([1, 2])
with col_pdf:
    if st.button("📄 Generar Reporte PDF", type="primary", use_container_width=True):
        try:
            with st.spinner("Generando resumen general..."):
                resumen = generate_resumen_general(sessions)
            st.session_state["report_resumen"] = resumen
            st.session_state["report_client"] = selected_name
            st.session_state["report_sessions"] = sessions
            st.session_state["report_pdf"] = None
            st.rerun()
        except Exception:
            st.error("Error al generar el resumen. Por favor intenta de nuevo.")

# Show preview if a resumen has been generated for this client
if (st.session_state.get("report_resumen")
        and st.session_state.get("report_client") == selected_name):
    st.markdown("---")
    st.subheader("📋 Vista previa del Resumen General")
    st.markdown(st.session_state["report_resumen"])

    feedback = st.text_area(
        "¿Tienes algún comentario o corrección? (opcional)",
        placeholder="Ej: Enfatizar más los avances en autoestima, omitir detalles sobre...",
        key="report_feedback",
    )

    col_approve, col_regenerate, col_cancel = st.columns(3)
    with col_approve:
        if st.button("✅ Aprobar y generar PDF", type="primary", use_container_width=True):
            try:
                with st.spinner("Generando PDF final..."):
                    pdf_bytes = generate_pdf(
                        selected_name,
                        st.session_state["report_sessions"],
                        resumen_general=st.session_state["report_resumen"],
                    )
                st.session_state["report_pdf"] = pdf_bytes
            except Exception:
                st.error("Error al generar el PDF. Por favor intenta de nuevo.")

    with col_regenerate:
        if st.button("🔄 Regenerar con feedback", use_container_width=True):
            if not feedback:
                st.warning("Escribe tu feedback antes de regenerar.")
            else:
                try:
                    with st.spinner("Regenerando resumen con tu feedback..."):
                        new_resumen = generate_resumen_general(
                            st.session_state["report_sessions"],
                            feedback=feedback,
                        )
                    st.session_state["report_resumen"] = new_resumen
                    st.rerun()
                except Exception:
                    st.error("Error al regenerar el resumen. Por favor intenta de nuevo.")

    with col_cancel:
        if st.button("❌ Cancelar", use_container_width=True):
            for key in ["report_resumen", "report_client", "report_sessions", "report_pdf"]:
                st.session_state.pop(key, None)
            st.rerun()

    # Show download button if PDF was generated
    if st.session_state.get("report_pdf"):
        st.download_button(
            label="⬇️ Descargar PDF",
            data=st.session_state["report_pdf"],
            file_name=f"reporte_{selected_name.replace(' ', '_')}.pdf",
            mime="application/pdf",
        )

st.divider()

# --- Session list ---
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

for session in sessions:
    session_num = session.get("session_number", "?")
    session_date = session.get("recorded_at", "")[:10]
    label = f"Sesión {session_num} — {session_date}"

    with st.expander(label):
        summary = session.get("structured_summary", {})

        # Estado emocional as badge
        estado = summary.get("estado_emocional", "")
        if estado:
            st.markdown(
                f'<span class="emotion-badge">{estado}</span>',
                unsafe_allow_html=True,
            )
            st.markdown("")

        # Resumen as highlighted text
        resumen = summary.get("resumen_sesion", "")
        if resumen:
            st.markdown(
                f"""<div class="ui-card">
                    <span class="field-tag">📝 Resumen</span>
                    <p style="margin:0.5rem 0 0 0; color:#333;">{resumen}</p>
                </div>""",
                unsafe_allow_html=True,
            )

        # List fields
        for key in ["objetivos_trabajados", "obstaculos_identificados",
                     "avances_y_revelaciones", "compromisos_del_cliente", "temas_pendientes"]:
            value = summary.get(key, [])
            if isinstance(value, list) and value:
                icon = _field_icons.get(key, "")
                field_label = _field_labels.get(key, key)
                st.markdown(f"**{icon} {field_label}:**")
                for item in value:
                    st.markdown(f"- {item}")
