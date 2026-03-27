import streamlit as st
from services.database import get_all_clients, get_sessions_for_client
from services.pdf_generator import generate_pdf
from services.styles import inject_custom_css, render_sidebar_brand, page_header, metric_card

inject_custom_css()
render_sidebar_brand()

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

# --- PDF generation at top for easy access ---
col_pdf, col_spacer = st.columns([1, 2])
with col_pdf:
    if st.button("📄 Generar Reporte PDF", type="primary", use_container_width=True):
        try:
            with st.spinner("Generando reporte PDF..."):
                pdf_bytes = generate_pdf(selected_name, sessions)
            st.download_button(
                label="⬇️ Descargar PDF",
                data=pdf_bytes,
                file_name=f"reporte_{selected_name.replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception:
            st.error("Error al generar el PDF. Por favor intenta de nuevo.")

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
