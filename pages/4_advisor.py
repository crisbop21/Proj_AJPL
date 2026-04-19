import streamlit as st
from services.auth import check_password
from services.database import get_all_clients, get_sessions_for_client
from services.advisor import generate_advice
from services.styles import inject_custom_css, render_sidebar_brand, page_header

inject_custom_css()
render_sidebar_brand()
check_password()

page_header("🧭 Asesor", "Insights y referentes para inspirar tu trabajo con cada cliente")

# --- Seleccionar cliente ---
clients = get_all_clients()
if not clients:
    st.warning("No hay clientes registrados. Agrega uno en la página de **Clientes**.")
    st.stop()

client_options = {c["name"]: c["id"] for c in clients}
selected_name = st.selectbox(
    "Cliente",
    list(client_options.keys()),
    placeholder="Elige un cliente...",
)
selected_client_id = client_options[selected_name]

sessions = get_sessions_for_client(selected_client_id)

if not sessions:
    st.info("Este cliente aún no tiene sesiones registradas. Graba al menos una para recibir sugerencias.")
    st.stop()

st.caption(f"Basado en {len(sessions)} sesión(es) registrada(s) para este cliente.")

focus = st.text_input(
    "¿Quieres enfocar las sugerencias en algo específico? (opcional)",
    placeholder="Ej: autoestima, relaciones, manejo de estrés...",
    key="advisor_focus",
)

col_run, col_clear = st.columns([1, 3])
with col_run:
    if st.button("💡 Generar sugerencias", type="primary", use_container_width=True):
        try:
            with st.spinner("Analizando sesiones y preparando sugerencias..."):
                advice = generate_advice(selected_name, sessions, focus=focus)
            st.session_state["advisor_result"] = advice
            st.session_state["advisor_client"] = selected_name
        except Exception:
            st.error("Error al generar sugerencias. Por favor intenta de nuevo.")

# --- Display results ---
if (st.session_state.get("advisor_result")
        and st.session_state.get("advisor_client") == selected_name):
    advice = st.session_state["advisor_result"]

    st.markdown("---")

    patrones = advice.get("patrones_observados", [])
    if patrones:
        st.markdown("### 🔍 Patrones observados")
        for item in patrones:
            st.markdown(f"- {item}")

    enfoques = advice.get("enfoques_sugeridos", [])
    if enfoques:
        st.markdown("### 🎯 Enfoques sugeridos para próximas sesiones")
        for item in enfoques:
            st.markdown(f"- {item}")

    ejercicios = advice.get("ejercicios_recomendados", [])
    if ejercicios:
        st.markdown("### 📝 Ejercicios recomendados")
        for item in ejercicios:
            st.markdown(f"- {item}")

    alertas = advice.get("senales_de_alerta", [])
    if alertas:
        st.markdown("### ⚠️ Señales de alerta")
        st.warning(
            "Considera si alguna de estas señales requiere derivar al cliente "
            "con un profesional de salud mental."
        )
        for item in alertas:
            st.markdown(f"- {item}")

    referentes = advice.get("referentes_recomendados", [])
    if referentes:
        st.markdown("### 📚 Referentes a investigar como inspiración")
        st.caption(
            "Sugerencias generadas por IA. Verifica cada referente antes de aplicar "
            "sus ideas y adapta lo que resuene con tu estilo de coaching."
        )
        for ref in referentes:
            nombre = ref.get("nombre", "")
            enfoque = ref.get("enfoque", "")
            por_que = ref.get("por_que", "")
            recurso = ref.get("recurso_sugerido", "")
            with st.expander(f"**{nombre}** — {enfoque}" if enfoque else f"**{nombre}**"):
                if por_que:
                    st.markdown(f"**Por qué es relevante:** {por_que}")
                if recurso:
                    st.markdown(f"**Recurso sugerido:** {recurso}")

    st.markdown("---")
    st.caption(
        "💡 Las sugerencias son solo puntos de partida. Tu criterio clínico y tu relación "
        "con el cliente siempre son la guía principal."
    )

    if st.button("🗑️ Limpiar sugerencias", use_container_width=False):
        for key in ["advisor_result", "advisor_client", "advisor_focus"]:
            st.session_state.pop(key, None)
        st.rerun()
