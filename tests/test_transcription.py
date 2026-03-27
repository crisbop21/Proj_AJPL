"""Tests for services/transcription.py — ElevenLabs Scribe integration."""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from services.transcription import transcribe_audio


class TestTranscribeAudio:
    @patch("services.transcription.ElevenLabs")
    def test_returns_transcribed_text(self, mock_elevenlabs_cls):
        mock_client = MagicMock()
        mock_elevenlabs_cls.return_value = mock_client
        mock_client.speech_to_text.convert.return_value = MagicMock(
            text="Hola, esta es una prueba de transcripcion."
        )

        with patch("builtins.open", mock_open(read_data=b"fake audio data")):
            result = transcribe_audio("/tmp/test.wav")

        assert result == "Hola, esta es una prueba de transcripcion."

    @patch("services.transcription.ElevenLabs")
    def test_uses_scribe_v2_model(self, mock_elevenlabs_cls):
        mock_client = MagicMock()
        mock_elevenlabs_cls.return_value = mock_client
        mock_client.speech_to_text.convert.return_value = MagicMock(text="test")

        with patch("builtins.open", mock_open(read_data=b"audio")):
            transcribe_audio("/tmp/test.wav")

        call_kwargs = mock_client.speech_to_text.convert.call_args
        assert call_kwargs.kwargs.get("model_id") or call_kwargs[1].get("model_id") == "scribe_v2"

    @patch("services.transcription.ElevenLabs")
    def test_uses_spanish_language_code(self, mock_elevenlabs_cls):
        mock_client = MagicMock()
        mock_elevenlabs_cls.return_value = mock_client
        mock_client.speech_to_text.convert.return_value = MagicMock(text="test")

        with patch("builtins.open", mock_open(read_data=b"audio")):
            transcribe_audio("/tmp/test.wav")

        call_kwargs = mock_client.speech_to_text.convert.call_args
        assert call_kwargs.kwargs.get("language_code") or call_kwargs[1].get("language_code") == "es"

    @patch("services.transcription.ElevenLabs")
    def test_uses_api_key_from_secrets(self, mock_elevenlabs_cls):
        mock_client = MagicMock()
        mock_elevenlabs_cls.return_value = mock_client
        mock_client.speech_to_text.convert.return_value = MagicMock(text="test")

        with patch("builtins.open", mock_open(read_data=b"audio")):
            transcribe_audio("/tmp/test.wav")

        mock_elevenlabs_cls.assert_called_once_with(api_key="el-test-fake-key")

    @patch("services.transcription.ElevenLabs")
    def test_raises_on_api_error(self, mock_elevenlabs_cls):
        mock_client = MagicMock()
        mock_elevenlabs_cls.return_value = mock_client
        mock_client.speech_to_text.convert.side_effect = Exception("API error")

        with patch("builtins.open", mock_open(read_data=b"audio")):
            with pytest.raises(Exception, match="API error"):
                transcribe_audio("/tmp/test.wav")
