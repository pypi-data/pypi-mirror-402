from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch

from ecp_reference.llm_ollama import (
    DEFAULT_OLLAMA_HOST,
    DEFAULT_OLLAMA_MODEL,
    ollama_chat_completion,
)


class TestOllamaChatCompletion(unittest.TestCase):
    """Tests for the Ollama chat completion function."""

    def test_ollama_chat_completion_success(self):
        """Test successful Ollama chat completion."""
        mock_response = json.dumps({
            "message": {
                "role": "assistant",
                "content": "This is the test response.",
            }
        }).encode("utf-8")

        mock_resp = MagicMock()
        mock_resp.read.return_value = mock_response
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
            result = ollama_chat_completion(
                model="llama3.2",
                messages=[
                    {"role": "system", "content": "You are helpful."},
                    {"role": "user", "content": "Hello!"},
                ],
                timeout_seconds=30,
            )

            self.assertEqual(result, "This is the test response.")

            # Verify the request was made correctly
            mock_urlopen.assert_called_once()
            call_args = mock_urlopen.call_args
            request = call_args[0][0]
            self.assertIn("/api/chat", request.full_url)

            # Verify the payload
            payload = json.loads(request.data.decode("utf-8"))
            self.assertEqual(payload["model"], "llama3.2")
            self.assertEqual(len(payload["messages"]), 2)
            self.assertFalse(payload["stream"])

    def test_ollama_connection_error(self):
        """Test handling when Ollama server is not running."""
        import urllib.error

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

            with self.assertRaises(RuntimeError) as ctx:
                ollama_chat_completion(
                    model="llama3.2",
                    messages=[{"role": "user", "content": "test"}],
                )

            self.assertIn("Connection refused", str(ctx.exception))
            self.assertIn("Is Ollama running", str(ctx.exception))

    def test_ollama_timeout(self):
        """Test timeout handling."""
        import socket
        import urllib.error

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError(socket.timeout("timed out"))

            with self.assertRaises(RuntimeError) as ctx:
                ollama_chat_completion(
                    model="llama3.2",
                    messages=[{"role": "user", "content": "test"}],
                    timeout_seconds=1,
                )

            self.assertIn("timed out", str(ctx.exception))

    def test_ollama_http_error(self):
        """Test HTTP error handling."""
        import urllib.error

        with patch("urllib.request.urlopen") as mock_urlopen:
            error = urllib.error.HTTPError(
                "http://localhost:11434/api/chat",
                404,
                "Not Found",
                {},
                None,
            )
            mock_urlopen.side_effect = error

            with self.assertRaises(RuntimeError) as ctx:
                ollama_chat_completion(
                    model="llama3.2",
                    messages=[{"role": "user", "content": "test"}],
                )

            self.assertIn("HTTP 404", str(ctx.exception))

    def test_ollama_with_options(self):
        """Test that max_tokens and temperature are passed as options."""
        mock_response = json.dumps({
            "message": {"role": "assistant", "content": "response"}
        }).encode("utf-8")

        mock_resp = MagicMock()
        mock_resp.read.return_value = mock_response
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
            ollama_chat_completion(
                model="llama3.2",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=100,
                temperature=0.7,
            )

            call_args = mock_urlopen.call_args
            request = call_args[0][0]
            payload = json.loads(request.data.decode("utf-8"))

            self.assertIn("options", payload)
            self.assertEqual(payload["options"]["num_predict"], 100)
            self.assertEqual(payload["options"]["temperature"], 0.7)

    def test_ollama_default_values(self):
        """Test that default host and model are used when not specified."""
        self.assertEqual(DEFAULT_OLLAMA_HOST, "http://localhost:11434")
        self.assertEqual(DEFAULT_OLLAMA_MODEL, "llama3.2")

    def test_ollama_custom_host(self):
        """Test using a custom host."""
        mock_response = json.dumps({
            "message": {"role": "assistant", "content": "response"}
        }).encode("utf-8")

        mock_resp = MagicMock()
        mock_resp.read.return_value = mock_response
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
            ollama_chat_completion(
                model="llama3.2",
                messages=[{"role": "user", "content": "test"}],
                host="http://custom-host:11434",
            )

            call_args = mock_urlopen.call_args
            request = call_args[0][0]
            self.assertTrue(request.full_url.startswith("http://custom-host:11434"))

    def test_ollama_invalid_response_format(self):
        """Test handling of invalid response format."""
        mock_response = json.dumps({"unexpected": "format"}).encode("utf-8")

        mock_resp = MagicMock()
        mock_resp.read.return_value = mock_response
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            with self.assertRaises(RuntimeError) as ctx:
                ollama_chat_completion(
                    model="llama3.2",
                    messages=[{"role": "user", "content": "test"}],
                )

            self.assertIn("missing message", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
