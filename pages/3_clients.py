import streamlit as st
from services.database import get_all_clients, add_client

st.title("Clientes")

# --- Formulario para agregar nuevo cliente ---
st.subheader("Agregar nuevo cliente")
with st.form("add_client_form"):
    name = st.text_input("Nombre del cliente *")
    notes = st.text_area("Notas (opcional)")
    submitted = st.form_submit_button("Agregar cliente")

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

# --- Lista de clientes ---
st.subheader("Lista de clientes")
clients = get_all_clients()

if not clients:
    st.info("No hay clientes registrados todavía.")
else:
    for client in clients:
        created = client.get("created_at", "")[:10]
        notes_text = client.get("notes", "") or ""
        label = f"**{client['name']}** — Registrado: {created}"
        if notes_text:
            label += f"  \nNotas: {notes_text}"
        st.markdown(label)
        st.divider()
