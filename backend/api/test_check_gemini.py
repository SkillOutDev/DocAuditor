from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

import httpx
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase
from google.genai.errors import ClientError

from api.ai import MissingGeminiAPIKey


class CheckGeminiCommandTests(SimpleTestCase):
    def setUp(self):
        self.provider = Mock()
        self.provider.model = "gemini-test"
        self.provider.client.models.list.return_value = [
            SimpleNamespace(name="models/one"),
            SimpleNamespace(name="models/two"),
        ]
        self.output = StringIO()

    def test_lists_models_without_generating(self):
        with patch("api.management.commands.check_gemini.GeminiProvider", return_value=self.provider):
            call_command("check_gemini", stdout=self.output)
        self.assertIn("Configured model: gemini-test", self.output.getvalue())
        self.assertIn("models/one", self.output.getvalue())
        self.assertIn("models/two", self.output.getvalue())
        self.assertIn("listing succeeded (2 models)", self.output.getvalue())
        self.provider.generate.assert_not_called()

    def test_optional_generation(self):
        self.provider.generate.return_value = "Hello"
        with patch("api.management.commands.check_gemini.GeminiProvider", return_value=self.provider):
            call_command("check_gemini", generate=True, stdout=self.output)
        self.provider.generate.assert_called_once_with("Say hello in one word.")
        self.assertIn("Gemini generation succeeded", self.output.getvalue())

    def test_empty_generation_fails(self):
        self.provider.generate.return_value = " "
        with patch("api.management.commands.check_gemini.GeminiProvider", return_value=self.provider):
            with self.assertRaisesMessage(CommandError, "empty generation response"):
                call_command("check_gemini", generate=True, stdout=self.output)

    def test_missing_key_fails(self):
        with patch("api.management.commands.check_gemini.GeminiProvider", side_effect=MissingGeminiAPIKey):
            with self.assertRaisesMessage(CommandError, "GEMINI_API_KEY is missing or empty"):
                call_command("check_gemini", stdout=self.output)

    def test_api_error_reports_status_without_sensitive_details(self):
        self.provider.client.models.list.side_effect = ClientError(
            404, {"error": {"message": "secret provider detail"}}
        )
        with patch("api.management.commands.check_gemini.GeminiProvider", return_value=self.provider):
            with self.assertRaises(CommandError) as error:
                call_command("check_gemini", stdout=self.output)
        self.assertIn("HTTP 404", str(error.exception))
        self.assertNotIn("secret provider detail", str(error.exception))

    def test_connection_error_does_not_expose_details(self):
        self.provider.client.models.list.side_effect = httpx.ConnectError("secret URL")
        with patch("api.management.commands.check_gemini.GeminiProvider", return_value=self.provider):
            with self.assertRaises(CommandError) as error:
                call_command("check_gemini", stdout=self.output)
        self.assertIn("ConnectError", str(error.exception))
        self.assertNotIn("secret URL", str(error.exception))
