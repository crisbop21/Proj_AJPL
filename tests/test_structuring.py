"""Tests for services/structuring.py — Claude structuring integration."""

import json
import pytest
from unittest.mock import patch, MagicMock
import anthropic
from services.structuring import structure_notes, _extract_json


class TestExtractJson:
    def test_parses_plain_json(self, sample_structured_summary):
        raw = json.dumps(sample_structured_summary)
        result = _extract_json(raw)
        assert result == sample_structured_summary

    def test_parses_json_wrapped_in_code_block(self, sample_structured_summary):
        raw = f"```json\n{json.dumps(sample_structured_summary)}\n```"
        result = _extract_json(raw)
        assert result == sample_structured_summary

    def test_parses_json_wrapped_in_plain_code_block(self, sample_structured_summary):
        raw = f"```\n{json.dumps(sample_structured_summary)}\n```"
        result = _extract_json(raw)
        assert result == sample_structured_summary

    def test_raises_on_invalid_json(self):
        with pytest.raises(json.JSONDecodeError):
            _extract_json("this is not json")

    def test_handles_whitespace_around_json(self, sample_structured_summary):
        raw = f"  \n  {json.dumps(sample_structured_summary)}  \n  "
        result = _extract_json(raw)
        assert result == sample_structured_summary


class TestStructureNotes:
    @patch("services.structuring.anthropic.Anthropic")
    def test_returns_structured_dict_with_all_7_fields(self, mock_anthropic_cls, sample_structured_summary):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text=json.dumps(sample_structured_summary))]
        )

        result = structure_notes("Transcripcion de prueba")

        assert isinstance(result, dict)
        expected_keys = [
            "resumen_sesion",
            "objetivos_trabajados",
            "obstaculos_identificados",
            "avances_y_revelaciones",
            "compromisos_del_cliente",
            "temas_pendientes",
            "estado_emocional",
        ]
        for key in expected_keys:
            assert key in result

    @patch("services.structuring.anthropic.Anthropic")
    def test_uses_correct_model(self, mock_anthropic_cls, sample_structured_summary):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text=json.dumps(sample_structured_summary))]
        )

        structure_notes("test")

        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-sonnet-4-20250514"

    @patch("services.structuring.anthropic.Anthropic")
    def test_uses_api_key_from_secrets(self, mock_anthropic_cls, sample_structured_summary):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text=json.dumps(sample_structured_summary))]
        )

        structure_notes("test")

        mock_anthropic_cls.assert_called_once_with(api_key="sk-ant-test-fake-key")

    @patch("services.structuring.anthropic.Anthropic")
    def test_retries_on_json_parse_failure(self, mock_anthropic_cls, sample_structured_summary):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        # First call returns invalid JSON, retry returns valid JSON
        mock_client.messages.create.side_effect = [
            MagicMock(content=[MagicMock(text="not valid json at all")]),
            MagicMock(content=[MagicMock(text=json.dumps(sample_structured_summary))]),
        ]

        result = structure_notes("test")
        assert result == sample_structured_summary
        assert mock_client.messages.create.call_count == 2

    @patch("services.structuring.anthropic.Anthropic")
    def test_raises_authentication_error_with_clear_message(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.side_effect = anthropic.AuthenticationError(
            message="invalid x-api-key",
            response=MagicMock(status_code=401),
            body={"error": {"type": "authentication_error", "message": "invalid x-api-key"}},
        )

        with pytest.raises(anthropic.AuthenticationError):
            structure_notes("test")

    @patch("services.structuring.anthropic.Anthropic")
    def test_handles_code_block_wrapped_response(self, mock_anthropic_cls, sample_structured_summary):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        wrapped = f"```json\n{json.dumps(sample_structured_summary)}\n```"
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text=wrapped)]
        )

        result = structure_notes("test")
        assert result == sample_structured_summary
