"""Tests for services/pdf_generator.py — PDF report generation."""

import pytest
from unittest.mock import patch, MagicMock
from services.pdf_generator import generate_pdf, _generate_resumen_general


class TestGenerateResumenGeneral:
    @patch("services.pdf_generator.anthropic.Anthropic")
    def test_returns_string_summary(self, mock_anthropic_cls, sample_sessions):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="Resumen general de las sesiones del cliente.")]
        )

        result = _generate_resumen_general(sample_sessions)
        assert isinstance(result, str)
        assert len(result) > 0

    @patch("services.pdf_generator.anthropic.Anthropic")
    def test_returns_fallback_on_error(self, mock_anthropic_cls, sample_sessions):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API error")

        result = _generate_resumen_general(sample_sessions)
        assert result == "No se pudo generar el resumen general."

    @patch("services.pdf_generator.anthropic.Anthropic")
    def test_handles_string_structured_summary(self, mock_anthropic_cls, sample_structured_summary):
        """Sessions where structured_summary is stored as a JSON string."""
        import json
        sessions = [{
            "session_number": 1,
            "structured_summary": json.dumps(sample_structured_summary),
            "recorded_at": "2026-01-15T10:00:00+00:00",
        }]

        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="Resumen del cliente.")]
        )

        result = _generate_resumen_general(sessions)
        assert isinstance(result, str)


class TestGeneratePdf:
    @patch("services.pdf_generator._generate_resumen_general")
    def test_returns_bytes(self, mock_resumen, sample_sessions):
        mock_resumen.return_value = "Resumen general de prueba."

        result = generate_pdf("Ana Garcia", sample_sessions)
        assert isinstance(result, bytes)
        assert len(result) > 0

    @patch("services.pdf_generator._generate_resumen_general")
    def test_pdf_starts_with_valid_header(self, mock_resumen, sample_sessions):
        mock_resumen.return_value = "Resumen de prueba."

        result = generate_pdf("Ana Garcia", sample_sessions)
        assert result[:5] == b"%PDF-"

    @patch("services.pdf_generator._generate_resumen_general")
    def test_works_with_single_session(self, mock_resumen, sample_structured_summary):
        mock_resumen.return_value = "Resumen."
        sessions = [{
            "id": "sess-001",
            "client_id": "client-001",
            "raw_transcript": "Transcripcion.",
            "structured_summary": sample_structured_summary,
            "session_number": 1,
            "recorded_at": "2026-03-01T10:00:00+00:00",
        }]

        result = generate_pdf("Carlos Lopez", sessions)
        assert isinstance(result, bytes)
        assert result[:5] == b"%PDF-"

    @patch("services.pdf_generator._generate_resumen_general")
    def test_works_with_empty_sessions(self, mock_resumen):
        mock_resumen.return_value = "Sin sesiones."

        result = generate_pdf("Test Client", [])
        assert isinstance(result, bytes)

    @patch("services.pdf_generator._generate_resumen_general")
    def test_handles_string_structured_summary_in_sessions(self, mock_resumen, sample_structured_summary):
        """Ensure generate_pdf handles structured_summary stored as JSON string."""
        import json
        mock_resumen.return_value = "Resumen."
        sessions = [{
            "id": "sess-001",
            "client_id": "client-001",
            "raw_transcript": "Transcripcion.",
            "structured_summary": json.dumps(sample_structured_summary),
            "session_number": 1,
            "recorded_at": "2026-03-01T10:00:00+00:00",
        }]

        result = generate_pdf("Test Client", sessions)
        assert isinstance(result, bytes)
        assert result[:5] == b"%PDF-"

    @patch("services.pdf_generator._generate_resumen_general")
    def test_handles_missing_temas_pendientes(self, mock_resumen):
        """Sessions with no temas_pendientes should still produce valid PDF."""
        mock_resumen.return_value = "Resumen."
        sessions = [{
            "id": "sess-001",
            "client_id": "client-001",
            "raw_transcript": "Transcripcion.",
            "structured_summary": {
                "resumen_sesion": "Resumen de prueba",
                "objetivos_trabajados": [],
                "obstaculos_identificados": [],
                "avances_y_revelaciones": [],
                "compromisos_del_cliente": [],
                "temas_pendientes": [],
                "estado_emocional": "Tranquilo",
            },
            "session_number": 1,
            "recorded_at": "2026-03-01T10:00:00+00:00",
        }]

        result = generate_pdf("Test", sessions)
        assert isinstance(result, bytes)
