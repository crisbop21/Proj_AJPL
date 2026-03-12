import streamlit as st

st.set_page_config(page_title="Life Coach Notes", page_icon="🎙️", layout="wide")

st.title("🎙️ Life Coach Notes")
st.markdown(
    """
    Bienvenida a tu asistente de notas de coaching.

    Usa el menú lateral para navegar entre las secciones:

    - **Nueva Sesión** — Graba y estructura notas de voz después de cada sesión
    - **Historial** — Consulta sesiones anteriores y genera reportes PDF
    - **Clientes** — Administra tu lista de clientes
    """
)
