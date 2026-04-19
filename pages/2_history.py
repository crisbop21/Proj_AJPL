import streamlit as st
from services.auth import check_password
from services.database import get_all_clients, get_sessions_for_client, delete_session
from services.pdf_generator import generate_pdf, generate_report_sections
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

# --- PDF generation with editable report form ---
col_pdf, col_spacer = st.columns([1, 2])
with col_pdf:
    if st.button("📄 Preparar Reporte PDF", type="primary", use_container_width=True):
        try:
            with st.spinner("Generando borrador del reporte con IA..."):
                secciones = generate_report_sections(sessions)
            # Clear any stale form fields from a previous client/draft
            for key in ["report_nombre", "report_documento", "report_motivo",
                        "report_temas", "report_avances", "report_compromisos",
                        "report_firma", "report_feedback"]:
                st.session_state.pop(key, None)
            st.session_state["report_sections"] = secciones
            st.session_state["report_client"] = selected_name
            st.session_state["report_sessions"] = sessions
            st.session_state["report_pdf"] = None
            st.rerun()
        except Exception:
            st.error("Error al generar el borrador. Por favor intenta de nuevo.")

# Show the editable form if a draft has been generated for this client
if (st.session_state.get("report_sections")
        and st.session_state.get("report_client") == selected_name):
    st.markdown("---")
    st.subheader("📋 Revisa y edita el reporte antes de exportar")
    st.caption("Puedes ajustar cualquier campo. Los textos fueron generados con IA como punto de partida.")

    secciones = st.session_state["report_sections"]

    # Initialize widget-bound keys once so Streamlit doesn't warn about value+key conflict
    st.session_state.setdefault("report_nombre", selected_name)
    st.session_state.setdefault("report_documento", "")
    st.session_state.setdefault("report_motivo", secciones.get("motivo_consulta", ""))
    st.session_state.setdefault("report_temas", secciones.get("resumen_temas_trabajados", ""))
    st.session_state.setdefault("report_avances", secciones.get("avances", ""))
    st.session_state.setdefault("report_compromisos", secciones.get("compromisos_y_recomendaciones", ""))
    st.session_state.setdefault("report_firma", "")

    col_a, col_b = st.columns(2)
    with col_a:
        nombre_cliente = st.text_input("Nombre del cliente", key="report_nombre")
    with col_b:
        documento = st.text_input(
            "Documento de identidad",
            key="report_documento",
            placeholder="Ej: CC 1.234.567",
        )

    motivo = st.text_area("Motivo de consulta", key="report_motivo", height=90)

    col_n, col_f = st.columns(2)
    with col_n:
        st.text_input("Número de sesiones", value=str(len(sessions)), disabled=True)
    with col_f:
        st.text_input("Fecha de la última sesión", value=last_date, disabled=True)

    temas = st.text_area("Resumen de temas trabajados", key="report_temas", height=140)
    avances = st.text_area("Avances", key="report_avances", height=140)
    compromisos = st.text_area(
        "Compromisos y recomendaciones", key="report_compromisos", height=140,
    )
    firma = st.text_input(
        "Firma", key="report_firma", placeholder="Ej: Ana Martínez — Coach de Vida",
    )

    feedback = st.text_area(
        "¿Quieres regenerar con la IA? Escribe feedback aquí (opcional)",
        placeholder="Ej: Enfatizar más los avances en autoestima, omitir detalles sobre...",
        key="report_feedback",
    )

    col_approve, col_regenerate, col_cancel = st.columns(3)
    with col_approve:
        if st.button("✅ Generar PDF", type="primary", use_container_width=True):
            try:
                with st.spinner("Generando PDF final..."):
                    pdf_bytes = generate_pdf(
                        client_name=nombre_cliente,
                        sessions=st.session_state["report_sessions"],
                        documento_identidad=documento,
                        motivo_consulta=motivo,
                        resumen_temas_trabajados=temas,
                        avances=avances,
                        compromisos_y_recomendaciones=compromisos,
                        firma=firma,
                    )
                st.session_state["report_pdf"] = pdf_bytes
            except Exception:
                st.error("Error al generar el PDF. Por favor intenta de nuevo.")

    with col_regenerate:
        if st.button("🔄 Regenerar con IA", use_container_width=True):
            if not feedback:
                st.warning("Escribe tu feedback antes de regenerar.")
            else:
                try:
                    with st.spinner("Regenerando con tu feedback..."):
                        nuevas = generate_report_sections(
                            st.session_state["report_sessions"],
                            feedback=feedback,
                        )
                    st.session_state["report_sections"] = nuevas
                    for key in ["report_motivo", "report_temas", "report_avances", "report_compromisos"]:
                        st.session_state.pop(key, None)
                    st.rerun()
                except Exception:
                    st.error("Error al regenerar. Por favor intenta de nuevo.")

    with col_cancel:
        if st.button("❌ Cancelar", use_container_width=True):
            for key in ["report_sections", "report_client", "report_sessions", "report_pdf",
                        "report_nombre", "report_documento", "report_motivo", "report_temas",
                        "report_avances", "report_compromisos", "report_firma", "report_feedback"]:
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

        # --- Delete session ---
        st.divider()
        session_id = session.get("id")
        confirm_key = f"confirm_delete_{session_id}"

        if st.session_state.get(confirm_key):
            st.warning(
                f"¿Seguro que deseas eliminar la Sesión {session_num}? "
                "Esta acción no se puede deshacer."
            )
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button(
                    "Sí, eliminar",
                    key=f"confirm_yes_{session_id}",
                    type="primary",
                    use_container_width=True,
                ):
                    try:
                        delete_session(session_id)
                        st.session_state.pop(confirm_key, None)
                        for key in ["report_resumen", "report_client",
                                    "report_sessions", "report_pdf"]:
                            st.session_state.pop(key, None)
                        st.success(f"Sesión {session_num} eliminada.")
                        st.rerun()
                    except Exception:
                        st.session_state.pop(confirm_key, None)
            with col_no:
                if st.button(
                    "Cancelar",
                    key=f"confirm_no_{session_id}",
                    use_container_width=True,
                ):
                    st.session_state.pop(confirm_key, None)
                    st.rerun()
        else:
            if st.button(
                "🗑️ Eliminar sesión",
                key=f"delete_{session_id}",
                use_container_width=True,
            ):
                st.session_state[confirm_key] = True
                st.rerun()
