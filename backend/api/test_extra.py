import json
import sys
import tempfile
from types import SimpleNamespace
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError
from django.test import TestCase, override_settings
from django.urls import reverse

from api import ai
from api.models import Document


class RegistrationValidationTests(TestCase):
    url = "/api/auth/register/"

    def post(self, payload, raw=False):
        body = payload if raw else json.dumps(payload)
        return self.client.post(self.url, body, content_type="application/json")

    def valid(self, **overrides):
        data = {"username": "jonas", "email": "Jonas@Example.com", "password": "longenough1"}
        data.update(overrides)
        return data

    def test_malformed_json_is_rejected(self):
        self.assertEqual(self.post("{not json", raw=True).status_code, 400)

    def test_non_object_json_is_rejected(self):
        self.assertEqual(self.post([1, 2]).status_code, 400)

    def test_field_validation_errors(self):
        cases = [
            ({"username": ""}, "username"),
            ({"username": "x" * 151}, "username"),
            ({"email": 5}, "email"),
            ({"email": "not-an-email"}, "email"),
            ({"email": "a" * 250 + "@x.lt"}, "email"),
            ({"password": "short"}, "password"),
            ({"password": "p" * 129}, "password"),
        ]
        for overrides, field in cases:
            with self.subTest(overrides=overrides):
                response = self.post(self.valid(**overrides))
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.json()["errors"])

    def test_username_with_invalid_characters_is_rejected(self):
        response = self.post(self.valid(username="bad name!"))
        self.assertEqual(response.status_code, 400)
        self.assertIn("username", response.json()["errors"])

    def test_duplicate_username_and_email_are_rejected(self):
        self.assertEqual(self.post(self.valid()).status_code, 201)
        self.assertEqual(self.post(self.valid(email="other@example.com", username="JONAS")).status_code, 409)
        response = self.post(self.valid(username="kitas"))
        self.assertEqual(response.status_code, 409)
        self.assertIn("email", response.json()["errors"])

    def test_integrity_error_during_create_returns_conflict(self):
        from django.db import IntegrityError

        with mock.patch.object(
            get_user_model().objects, "create_user", side_effect=IntegrityError
        ):
            self.assertEqual(self.post(self.valid()).status_code, 409)


class LoginEdgeCaseTests(TestCase):
    url = "/api/auth/login/"

    def post(self, body, raw=False):
        data = body if raw else json.dumps(body)
        return self.client.post(self.url, data, content_type="application/json")

    def test_invalid_payloads_return_401(self):
        payloads = [
            ("{bad", True),
            ([1], False),
            ({"email": 1, "password": "x"}, False),
            ({"email": "", "password": "x"}, False),
            ({"email": "a@b.lt", "password": ""}, False),
            ({"email": "a" * 300, "password": "x"}, False),
            ({"email": "a@b.lt", "password": "p" * 200}, False),
        ]
        for body, raw in payloads:
            with self.subTest(body=body):
                response = self.post(body, raw)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.json()["message"], "Neteisingai suvesti prisijungimo duomenys")


class MiscViewTests(TestCase):
    def test_health_endpoint(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)

    def test_csrf_endpoint_sets_cookie(self):
        response = self.client.get(reverse("csrf"))
        self.assertIn("csrftoken", response.cookies)


class DocumentEdgeCaseTests(TestCase):
    def setUp(self):
        media = tempfile.TemporaryDirectory()
        self.addCleanup(media.cleanup)
        settings_override = override_settings(MEDIA_ROOT=media.name)
        settings_override.enable()
        self.addCleanup(settings_override.disable)
        User = get_user_model()
        self.user = User.objects.create_user(username="owner", password="pass-12345")
        self.other = User.objects.create_user(username="intruder", password="pass-12345")
        self.document = Document.objects.create(
            owner=self.user,
            title="doc",
            file=SimpleUploadedFile("doc.pdf", b"PDF"),
            original_filename="doc.pdf",
            file_size=3,
        )

    def test_upload_requires_exactly_one_file(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("documents"), {})
        self.assertEqual(response.status_code, 400)
        two = self.client.post(
            reverse("documents"),
            {"file": [SimpleUploadedFile("a.pdf", b"1"), SimpleUploadedFile("b.pdf", b"2")]},
        )
        self.assertEqual(two.status_code, 400)

    def test_upload_strips_directories_from_filename(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("documents"),
            {"file": SimpleUploadedFile("C:\\temp\\nested.pdf", b"PDF")},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["document"]["original_filename"], "nested.pdf")

    def test_preview_requires_login(self):
        response = self.client.get(f"/api/documents/{self.document.pk}/preview/")
        self.assertEqual(response.status_code, 401)

    def test_preview_unknown_document_is_404(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/api/documents/9999/preview/").status_code, 404)

    def test_preview_with_missing_file_is_404(self):
        self.client.force_login(self.user)
        self.document.file.delete(save=False)
        self.assertEqual(self.client.get(f"/api/documents/{self.document.pk}/preview/").status_code, 404)

    def test_preview_with_unreadable_file_is_404(self):
        self.client.force_login(self.user)
        with mock.patch("django.db.models.fields.files.FieldFile.open", side_effect=OSError):
            response = self.client.get(f"/api/documents/{self.document.pk}/preview/")
        self.assertEqual(response.status_code, 404)

    def test_delete_requires_login(self):
        response = self.client.delete(f"/api/documents/{self.document.pk}/")
        self.assertEqual(response.status_code, 401)

    def test_owner_can_delete_document_and_file(self):
        self.client.force_login(self.user)
        path = self.document.file.path
        response = self.client.delete(f"/api/documents/{self.document.pk}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Document.objects.filter(pk=self.document.pk).exists())
        from pathlib import Path

        self.assertFalse(Path(path).exists())

    def test_cannot_delete_someone_elses_document(self):
        self.client.force_login(self.other)
        response = self.client.delete(f"/api/documents/{self.document.pk}/")
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Document.objects.filter(pk=self.document.pk).exists())

    def test_delete_failure_returns_500(self):
        self.client.force_login(self.user)
        with mock.patch.object(Document, "delete", side_effect=DatabaseError):
            response = self.client.delete(f"/api/documents/{self.document.pk}/")
        self.assertEqual(response.status_code, 500)


class DocumentModelTests(TestCase):
    def test_string_representation_and_validators(self):
        from django.core.exceptions import ValidationError

        from api.models import validate_document_file

        user = get_user_model().objects.create_user(username="m", password="pass-12345")
        document = Document(owner=user, title="Sutartis", original_filename="s.pdf")
        self.assertIn("Sutartis", str(document))
        with self.assertRaises(ValidationError):
            validate_document_file(SimpleUploadedFile("x.exe", b"1"))
        validate_document_file(SimpleUploadedFile("x.docx", b"1"))


class AIProviderTests(TestCase):
    def test_get_ai_provider_selects_ollama_by_default(self):
        with mock.patch.dict("os.environ", clear=False) as env:
            env.pop("AI_PROVIDER", None)
            self.assertIsInstance(ai.get_ai_provider(), ai.OllamaProvider)

    def test_get_ai_provider_rejects_unknown_provider(self):
        with mock.patch.dict("os.environ", {"AI_PROVIDER": "nope"}):
            with self.assertRaises(ValueError):
                ai.get_ai_provider()

    def test_ollama_generate_posts_prompt(self):
        response = mock.Mock()
        response.json.return_value = {"response": "atsakymas"}
        with mock.patch.dict(
            "os.environ", {"OLLAMA_BASE_URL": "http://ollama:1/", "OLLAMA_MODEL": "m"}
        ), mock.patch("api.ai.requests.post", return_value=response) as post:
            provider = ai.OllamaProvider()
            self.assertEqual(provider.generate("labas"), "atsakymas")
        post.assert_called_once()
        self.assertEqual(post.call_args.args[0], "http://ollama:1/api/generate")
        self.assertEqual(post.call_args.kwargs["json"]["prompt"], "labas")
        response.raise_for_status.assert_called_once()

    def test_gemini_provider_returns_text(self):
        client = mock.Mock()
        client.models.generate_content.return_value = SimpleNamespace(text="gemini")
        genai = SimpleNamespace(Client=mock.Mock(return_value=client))
        google = SimpleNamespace(genai=genai)
        with mock.patch.dict(sys.modules, {"google": google, "google.genai": genai}), mock.patch.dict(
            "os.environ", {"AI_PROVIDER": "gemini", "GEMINI_API_KEY": "k"}
        ):
            provider = ai.get_ai_provider()
            self.assertEqual(provider.generate("hi"), "gemini")
            client.models.generate_content.return_value = SimpleNamespace(text=None)
            self.assertEqual(provider.generate("hi"), "")
