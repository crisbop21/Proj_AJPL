"""Tests for services/pdf_generator.py — PDF report generation."""

import json
import pytest
from unittest.mock import patch, MagicMock
from services.pdf_generator import generate_pdf, generate_report_sections


SECTIONS_KEYS = [
    "motivo_consulta",
    "resumen_temas_trabajados",
    "avances",
    "compromisos_y_recomendaciones",
]


def _mock_claude_response(text: str) -> MagicMock:
    return MagicMock(content=[MagicMock(text=text)])


def _sample_sections_json() -> str:
    return json.dumps({
        "motivo_consulta": "El cliente busca claridad profesional.",
        "resumen_temas_trabajados": "Se trabajaron metas de carrera y comunicacion.",
        "avances": "Reconocio patrones limitantes.",
        "compromisos_y_recomendaciones": "Ejercicio diario y escritura en diario.",
    })


class TestGenerateReportSections:
    @patch("services.pdf_generator.anthropic.Anthropic")
    def test_returns_dict_with_all_sections(self, mock_anthropic_cls, sample_sessions):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _mock_claude_response(
            _sample_sections_json()
        )

        result = generate_report_sections(sample_sessions)
        assert isinstance(result, dict)
        for key in SECTIONS_KEYS:
            assert key in result
            assert isinstance(result[key], str)
            assert len(result[key]) > 0

    @patch("services.pdf_generator.st")
    @patch("services.pdf_generator.anthropic.Anthropic")
    def test_returns_fallback_on_error(self, mock_anthropic_cls, mock_st, sample_sessions):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API error")

        result = generate_report_sections(sample_sessions)
        assert result == {key: "" for key in SECTIONS_KEYS}
        mock_st.error.assert_called_once()

    @patch("services.pdf_generator.anthropic.Anthropic")
    def test_handles_json_in_code_fences(self, mock_anthropic_cls, sample_sessions):
        """Claude sometimes wraps output in ```json fences despite instructions."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _mock_claude_response(
            f"```json\n{_sample_sections_json()}\n```"
        )

        result = generate_report_sections(sample_sessions)
        assert result["motivo_consulta"] == "El cliente busca claridad profesional."

    @patch("services.pdf_generator.anthropic.Anthropic")
    def test_handles_string_structured_summary(self, mock_anthropic_cls, sample_structured_summary):
        """Sessions where structured_summary is stored as a JSON string."""
        sessions = [{
            "session_number": 1,
            "structured_summary": json.dumps(sample_structured_summary),
            "recorded_at": "2026-01-15T10:00:00+00:00",
        }]

        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _mock_claude_response(
            _sample_sections_json()
        )

        result = generate_report_sections(sessions)
        assert isinstance(result, dict)
        for key in SECTIONS_KEYS:
            assert key in result

    @patch("services.pdf_generator.anthropic.Anthropic")
    def test_feedback_is_included_in_system_prompt(self, mock_anthropic_cls, sample_sessions):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _mock_claude_response(
            _sample_sections_json()
        )

        generate_report_sections(sample_sessions, feedback="Hazlo mas breve")
        _, kwargs = mock_client.messages.create.call_args
        assert "Hazlo mas breve" in kwargs["system"]


class TestGeneratePdf:
    def test_returns_bytes(self, sample_sessions):
        result = generate_pdf("Ana Garcia", sample_sessions)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_pdf_starts_with_valid_header(self, sample_sessions):
        result = generate_pdf("Ana Garcia", sample_sessions)
        assert result[:5] == b"%PDF-"

    def test_works_with_all_sections_filled(self, sample_sessions):
        result = generate_pdf(
            "Ana Garcia",
            sample_sessions,
            documento_identidad="CC 123456789",
            motivo_consulta="Claridad profesional.",
            resumen_temas_trabajados="Metas de carrera.",
            avances="Reconocio patrones.",
            compromisos_y_recomendaciones="Ejercicio diario.",
            firma="Coach Maria",
        )
        assert isinstance(result, bytes)
        assert result[:5] == b"%PDF-"

    def test_works_with_single_session(self, sample_structured_summary):
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

    def test_works_with_empty_sessions(self):
        result = generate_pdf("Test Client", [])
        assert isinstance(result, bytes)
        assert result[:5] == b"%PDF-"

    def test_handles_string_structured_summary_in_sessions(self, sample_structured_summary):
        """Ensure generate_pdf handles structured_summary stored as JSON string."""
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

    def test_handles_session_without_recorded_at(self, sample_structured_summary):
        """Sessions missing recorded_at should still produce a valid PDF."""
        sessions = [{
            "id": "sess-001",
            "client_id": "client-001",
            "raw_transcript": "Transcripcion.",
            "structured_summary": sample_structured_summary,
            "session_number": 1,
        }]

        result = generate_pdf("Test", sessions)
        assert isinstance(result, bytes)
        assert result[:5] == b"%PDF-"
