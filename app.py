import streamlit as st

st.set_page_config(page_title="Coach Notes", page_icon="🎙️", layout="wide")

from services.styles import inject_custom_css, render_sidebar_brand

inject_custom_css()
render_sidebar_brand()

# --- Hero section ---
st.markdown(
    """
    <div class="hero-section">
        <h1>🎙️ Coach Notes</h1>
        <p>Tu asistente inteligente para organizar, estructurar y dar seguimiento a tus sesiones de coaching.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# --- Feature cards ---
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">🎤</div>
            <h3>Nueva Sesión</h3>
            <p>Graba notas de voz y obtén un resumen estructurado con IA en segundos.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">📋</div>
            <h3>Historial</h3>
            <p>Consulta sesiones anteriores y genera reportes PDF profesionales.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">👥</div>
            <h3>Clientes</h3>
            <p>Administra tu lista de clientes y mantén sus datos organizados.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("")
st.markdown("")

st.markdown(
    '<p style="text-align:center; color:#aaa; font-size:0.85rem;">'
    "Selecciona una sección en el menú lateral para comenzar →"
    "</p>",
    unsafe_allow_html=True,
)
