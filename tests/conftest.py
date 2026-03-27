"""Shared fixtures for all tests.

Mocks st.secrets and external services so tests run without real credentials.
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def mock_streamlit_secrets(monkeypatch):
    """Mock st.secrets so no real credentials are needed."""
    secrets = {
        "ANTHROPIC_API_KEY": "sk-ant-test-fake-key",
        "ELEVENLABS_API_KEY": "el-test-fake-key",
        "SUPABASE_URL": "https://test-project.supabase.co",
        "SUPABASE_ANON_KEY": "eyJ-test-fake-key",
    }
    mock_secrets = MagicMock()
    mock_secrets.__getitem__ = lambda self, key: secrets[key]
    mock_secrets.__contains__ = lambda self, key: key in secrets
    monkeypatch.setattr("streamlit.secrets", mock_secrets)
    return mock_secrets


@pytest.fixture
def mock_supabase():
    """Returns a mock Supabase client with chainable table methods."""
    mock_client = MagicMock()

    # Make table() return a chainable mock
    table_mock = MagicMock()
    mock_client.table.return_value = table_mock

    # Chain: .select().order().execute()
    table_mock.select.return_value = table_mock
    table_mock.order.return_value = table_mock
    table_mock.eq.return_value = table_mock
    table_mock.insert.return_value = table_mock
    table_mock.delete.return_value = table_mock

    return mock_client


@pytest.fixture
def sample_structured_summary():
    """A valid structured summary dict matching the 7 coaching fields."""
    return {
        "resumen_sesion": "El cliente discutio sus objetivos de carrera.",
        "objetivos_trabajados": ["Definir metas profesionales", "Mejorar comunicacion"],
        "obstaculos_identificados": ["Miedo al cambio", "Falta de tiempo"],
        "avances_y_revelaciones": ["Reconocio patrones limitantes"],
        "compromisos_del_cliente": ["Hacer ejercicio diario", "Escribir en diario"],
        "temas_pendientes": ["Relacion con pareja", "Manejo de estres"],
        "estado_emocional": "Motivado pero ansioso",
    }


@pytest.fixture
def sample_sessions(sample_structured_summary):
    """A list of sample session dicts as returned from Supabase."""
    return [
        {
            "id": "sess-001",
            "client_id": "client-001",
            "raw_transcript": "Transcripcion de la sesion uno.",
            "structured_summary": sample_structured_summary,
            "session_number": 1,
            "recorded_at": "2026-01-15T10:00:00+00:00",
        },
        {
            "id": "sess-002",
            "client_id": "client-001",
            "raw_transcript": "Transcripcion de la sesion dos.",
            "structured_summary": sample_structured_summary,
            "session_number": 2,
            "recorded_at": "2026-02-20T10:00:00+00:00",
        },
    ]
