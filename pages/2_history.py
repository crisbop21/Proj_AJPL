import streamlit as st
from services.database import get_all_clients, get_sessions_for_client
from services.pdf_generator import generate_pdf

st.title("Historial")

# --- Seleccionar cliente ---
clients = get_all_clients()
if not clients:
    st.warning("No hay clientes registrados. Agrega uno en la página de Clientes.")
    st.stop()

client_options = {c["name"]: c["id"] for c in clients}
selected_name = st.selectbox("Seleccionar cliente", list(client_options.keys()))
selected_client_id = client_options[selected_name]

# --- Mostrar sesiones ---
sessions = get_sessions_for_client(selected_client_id)

if not sessions:
    st.info("Este cliente no tiene sesiones registradas.")
    st.stop()

st.write(f"**Total de sesiones:** {len(sessions)}")

for session in sessions:
    session_num = session.get("session_number", "?")
    session_date = session.get("recorded_at", "")[:10]
    label = f"Sesión {session_num} — {session_date}"

    with st.expander(label):
        summary = session.get("structured_summary", {})

        field_labels = {
            "resumen_sesion": "Resumen de la Sesión",
            "objetivos_trabajados": "Objetivos Trabajados",
            "obstaculos_identificados": "Obstáculos Identificados",
            "avances_y_revelaciones": "Avances y Revelaciones",
            "compromisos_del_cliente": "Compromisos del Cliente",
            "temas_pendientes": "Temas Pendientes",
            "estado_emocional": "Estado Emocional",
        }

        for key, field_label in field_labels.items():
            value = summary.get(key, "")
            if isinstance(value, list) and value:
                st.markdown(f"**{field_label}:**")
                for item in value:
                    st.markdown(f"- {item}")
            elif value:
                st.markdown(f"**{field_label}:** {value}")

# --- Generar PDF ---
if st.button("Generar Reporte PDF"):
    try:
        with st.spinner("Generando reporte PDF..."):
            pdf_bytes = generate_pdf(selected_name, sessions)
        st.download_button(
            label="Descargar PDF",
            data=pdf_bytes,
            file_name=f"reporte_{selected_name.replace(' ', '_')}.pdf",
            mime="application/pdf",
        )
    except Exception:
        st.error("Error al generar el PDF. Por favor intenta de nuevo.")
