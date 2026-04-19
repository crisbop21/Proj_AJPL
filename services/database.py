import streamlit as st
from supabase import create_client


def _get_client():
    """Crea una instancia del cliente Supabase."""
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])


def get_all_clients() -> list[dict]:
    """Obtiene todos los clientes ordenados por nombre."""
    try:
        supabase = _get_client()
        response = supabase.table("clients").select("*").order("name").execute()
        return response.data
    except Exception as e:
        st.error("Error al obtener la lista de clientes.")
        return []


def add_client(name: str, notes: str = "") -> None:
    """Agrega un nuevo cliente."""
    try:
        supabase = _get_client()
        supabase.table("clients").insert({"name": name, "notes": notes}).execute()
    except Exception as e:
        st.error("Error al agregar el cliente. Por favor intenta de nuevo.")
        raise


def delete_client(client_id: str) -> None:
    """Elimina un cliente por su ID. Las sesiones se eliminan en cascada."""
    try:
        supabase = _get_client()
        supabase.table("clients").delete().eq("id", client_id).execute()
    except Exception as e:
        st.error("Error al eliminar el cliente.")
        raise


def save_session(client_id: str, transcript: str, summary: dict) -> None:
    """Guarda una sesión con transcripción y resumen estructurado."""
    try:
        supabase = _get_client()
        supabase.table("sessions").insert({
            "client_id": client_id,
            "raw_transcript": transcript,
            "structured_summary": summary,
        }).execute()
    except Exception as e:
        st.error("Error al guardar la sesión. Por favor intenta de nuevo.")
        raise


def update_session(session_id: str, transcript: str, summary: dict) -> None:
    """Actualiza la transcripción y el resumen estructurado de una sesión existente."""
    try:
        supabase = _get_client()
        supabase.table("sessions").update({
            "raw_transcript": transcript,
            "structured_summary": summary,
        }).eq("id", session_id).execute()
    except Exception as e:
        st.error("Error al actualizar la sesión. Por favor intenta de nuevo.")
        raise


def get_sessions_for_client(client_id: str) -> list[dict]:
    """Obtiene todas las sesiones de un cliente en orden cronológico."""
    try:
        supabase = _get_client()
        response = (
            supabase.table("sessions")
            .select("*")
            .eq("client_id", client_id)
            .order("session_number")
            .execute()
        )
        return response.data
    except Exception as e:
        st.error("Error al obtener las sesiones.")
        return []


def delete_session(session_id: str) -> None:
    """Elimina una sesión por su ID."""
    try:
        supabase = _get_client()
        supabase.table("sessions").delete().eq("id", session_id).execute()
    except Exception as e:
        st.error("Error al eliminar la sesión.")
        raise
