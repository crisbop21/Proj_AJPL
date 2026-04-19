"""Password gate for the coaching app."""

import hmac
import streamlit as st


def check_password() -> None:
    """Block the page until the user enters the correct password.

    Reads the expected password from ``st.secrets["APP_PASSWORD"]`` and stores
    the authenticated state in ``st.session_state`` so the user only logs in
    once per browser session.
    """
    if st.session_state.get("auth_ok"):
        return

    expected = st.secrets.get("APP_PASSWORD")
    if not expected:
        st.error(
            "La aplicación no está configurada correctamente. "
            "Falta APP_PASSWORD en los secretos."
        )
        st.stop()

    st.markdown("### 🔒 Acceso restringido")
    st.caption("Por favor ingresa la contraseña para continuar.")

    with st.form("login_form", clear_on_submit=False):
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Entrar")

    if submitted:
        if hmac.compare_digest(password, expected):
            st.session_state["auth_ok"] = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta. Intenta de nuevo.")

    st.stop()
