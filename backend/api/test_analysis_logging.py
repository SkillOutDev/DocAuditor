from unittest.mock import Mock, patch

import requests
from django.test import SimpleTestCase
from google.genai.errors import ClientError

from api.ai import GeminiProvider, MissingGeminiAPIKey
from api.analysis import AnalysisError, generate_summary


class AnalysisLoggingTests(SimpleTestCase):
    def test_api_status_and_oversized_summary_are_logged_without_contents(self):
        private_text = "private document contents"
        private_summary = "S" * 2001
        gemini = Mock()
        gemini.generate.side_effect = ClientError(
            429, {"error": {"message": "secret provider detail", "status": "RESOURCE_EXHAUSTED"}}
        )
        ollama = Mock()
        ollama.generate.return_value = private_summary
        with patch("api.analysis.get_gemini_provider", return_value=gemini), \
             patch("api.analysis.OllamaProvider", return_value=ollama), \
             self.assertLogs("api.analysis", level="WARNING") as logs:
            with self.assertRaises(AnalysisError):
                generate_summary(private_text)
        output = "\n".join(logs.output)
        self.assertIn("Gemini analysis failed: API returned HTTP 429", output)
        self.assertIn("Ollama analysis returned 2001 characters; retrying", output)
        self.assertIn("Ollama analysis failed: summary is 2001 characters; maximum is 2000", output)
        self.assertEqual(ollama.generate.call_count, 2)
        self.assertNotIn(private_text, output)
        self.assertNotIn(private_summary, output)
        self.assertNotIn("secret provider detail", output)

    def test_fallback_http_status_and_missing_key_are_logged(self):
        response = requests.Response()
        response.status_code = 404
        ollama = Mock()
        ollama.generate.side_effect = requests.HTTPError("sensitive response", response=response)
        with patch("api.analysis.get_gemini_provider", side_effect=MissingGeminiAPIKey), \
             patch("api.analysis.OllamaProvider", return_value=ollama), \
             self.assertLogs("api.analysis", level="WARNING") as logs:
            with self.assertRaises(AnalysisError):
                generate_summary("document")
        output = "\n".join(logs.output)
        self.assertIn("GEMINI_API_KEY is missing or empty", output)
        self.assertIn("Ollama analysis failed: provider returned HTTP 404", output)
        self.assertNotIn("sensitive response", output)

    def test_empty_summary_and_connection_failure_are_logged(self):
        gemini = Mock()
        gemini.generate.return_value = " "
        ollama = Mock()
        ollama.generate.side_effect = requests.ConnectionError("private URL")
        with patch("api.analysis.get_gemini_provider", return_value=gemini), \
             patch("api.analysis.OllamaProvider", return_value=ollama), \
             self.assertLogs("api.analysis", level="WARNING") as logs:
            with self.assertRaises(AnalysisError):
                generate_summary("document")
        output = "\n".join(logs.output)
        self.assertIn("Gemini analysis failed: provider returned an empty summary", output)
        self.assertIn("Ollama analysis failed: could not connect to provider", output)
        self.assertNotIn("private URL", output)

    def test_empty_key_is_identified(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
            with self.assertRaises(MissingGeminiAPIKey):
                GeminiProvider()

    def test_ollama_retries_an_oversized_summary_once(self):
        ollama = Mock()
        ollama.generate.side_effect = ["x" * 2001, "Trumpos pagrindinės sąlygos."]
        with patch("api.analysis.get_gemini_provider", side_effect=MissingGeminiAPIKey), \
             patch("api.analysis.OllamaProvider", return_value=ollama), \
             self.assertLogs("api.analysis", level="WARNING"):
            result = generate_summary("Dokumento sąlygos")
        self.assertEqual(result, "Trumpos pagrindinės sąlygos.")
        self.assertEqual(ollama.generate.call_count, 2)
        prompts = [call.args[0] for call in ollama.generate.call_args_list]
        self.assertIn("about 50 words", prompts[0])
        self.assertIn("about 30 words", prompts[1])
        self.assertTrue(all("2000 characters" in p for p in prompts))
        self.assertTrue(all("in Lithuanian" in p for p in prompts))
        self.assertTrue(all("Start directly with" in p for p in prompts))
        self.assertTrue(all("<document>\nDokumento sąlygos\n</document>" in p for p in prompts))

    def test_gemini_prompt_is_english_and_requests_lithuanian_summary(self):
        gemini = Mock()
        gemini.generate.return_value = "Dokumente nurodytos mokėjimo sąlygos."
        with patch("api.analysis.get_gemini_provider", return_value=gemini):
            self.assertEqual(generate_summary("Mokėjimo sąlygos"), gemini.generate.return_value)
        prompt = gemini.generate.call_args.args[0]
        self.assertIn("Translate the relevant information into Lithuanian", prompt)
        self.assertIn("Start directly with the document's main point", prompt)
        self.assertIn("<document>\nMokėjimo sąlygos\n</document>", prompt)

    def test_ollama_accepts_up_to_2000_characters_without_retry(self):
        for length in (701, 1676, 2000):
            with self.subTest(length=length):
                ollama = Mock()
                ollama.generate.return_value = "x" * length
                with patch("api.analysis.get_gemini_provider", side_effect=MissingGeminiAPIKey), \
                     patch("api.analysis.OllamaProvider", return_value=ollama), \
                     self.assertLogs("api.analysis", level="WARNING"):
                    self.assertEqual(len(generate_summary("document")), length)
                ollama.generate.assert_called_once()
