import streamlit as st
from services.database import get_all_clients, add_client, delete_client
from services.styles import inject_custom_css, render_sidebar_brand, page_header, metric_card

inject_custom_css()
render_sidebar_brand()

page_header("👥 Clientes", "Administra tu lista de clientes")

# --- Metrics ---
clients = get_all_clients()
col_metric, _ = st.columns([1, 2])
with col_metric:
    metric_card(str(len(clients)), "Clientes registrados")

st.markdown("")

# --- Two-column layout: form on left, list on right ---
col_form, col_list = st.columns([1, 2])

with col_form:
    st.markdown("#### Agregar nuevo cliente")
    with st.form("add_client_form"):
        name = st.text_input("Nombre del cliente *")
        notes = st.text_area("Notas (opcional)", height=100)
        submitted = st.form_submit_button(
            "➕ Agregar cliente", type="primary", use_container_width=True
        )

        if submitted:
            if not name.strip():
                st.warning("El nombre del cliente es obligatorio.")
            else:
                try:
                    add_client(name.strip(), notes.strip())
                    st.success(f"Cliente '{name.strip()}' agregado correctamente.")
                    st.rerun()
                except Exception:
                    pass  # Error already shown by add_client

with col_list:
    st.markdown("#### Lista de clientes")

    if not clients:
        st.info("No hay clientes registrados todavía.")
    else:
        for client in clients:
            created = client.get("created_at", "")[:10]
            notes_text = client.get("notes", "") or ""
            client_id = client.get("id", "")

            notes_html = ""
            if notes_text:
                notes_html = f'<div class="client-notes">{notes_text}</div>'

            st.markdown(
                f"""<div class="client-card">
                    <div class="client-name">{client["name"]}</div>
                    <div class="client-meta">Registrado: {created}</div>
                    {notes_html}
                </div>""",
                unsafe_allow_html=True,
            )

            # Delete button in a small column
            if st.button("🗑️ Eliminar", key=f"del_{client_id}", help="Eliminar este cliente"):
                try:
                    delete_client(client_id)
                    st.rerun()
                except Exception:
                    pass  # Error already shown by delete_client
