import json
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from api.models import MAX_DOCUMENT_SIZE, Document


class DocumentStorageAPITests(TestCase):
    def setUp(self):
        self.media_directory = tempfile.TemporaryDirectory()
        self.media_settings = override_settings(MEDIA_ROOT=self.media_directory.name)
        self.media_settings.enable()
        self.addCleanup(self.media_directory.cleanup)
        self.addCleanup(self.media_settings.disable)
        self.user = get_user_model().objects.create_user(
            username="document-owner",
            password="secure-test-password",
        )
        self.url = reverse("documents")

    def test_anonymous_client_cannot_list_or_upload_documents(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

        response = self.client.post(
            self.url,
            {"file": SimpleUploadedFile("contract.pdf", b"PDF")},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Document.objects.count(), 0)

    def test_upload_saves_file_and_returns_document(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {"file": SimpleUploadedFile("contract.pdf", b"PDF content", content_type="application/pdf")},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["message"], "Dokumentas išsaugotas sėkmingai")
        document = Document.objects.get()
        self.assertEqual(document.owner, self.user)
        self.assertEqual(document.original_filename, "contract.pdf")
        self.assertEqual(document.analysis_status, Document.AnalysisStatus.PENDING)
        self.assertTrue(Path(document.file.path).is_file())

    def test_document_list_only_contains_current_users_documents(self):
        other_user = get_user_model().objects.create_user(
            username="another-owner",
            password="secure-test-password",
        )
        Document.objects.create(
            owner=self.user,
            title="My document",
            file=SimpleUploadedFile("my.pdf", b"PDF"),
            original_filename="my.pdf",
            file_size=3,
        )
        Document.objects.create(
            owner=other_user,
            title="Private document",
            file=SimpleUploadedFile("private.pdf", b"PDF"),
            original_filename="private.pdf",
            file_size=3,
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        documents = response.json()["documents"]
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0]["title"], "My document")

    def test_upload_rejects_unsupported_extension(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {"file": SimpleUploadedFile("notes.txt", b"text")},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "Nepavyko įkelti dokumento.")
        self.assertEqual(Document.objects.count(), 0)

    def test_upload_rejects_file_larger_than_15_mib(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {"file": SimpleUploadedFile("large.pdf", b"x" * (MAX_DOCUMENT_SIZE + 1))},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Document.objects.count(), 0)


class APIDocumentationTests(TestCase):
    def test_openapi_schema_documents_existing_endpoints(self):
        response = self.client.get(
            "/api/schema/",
            HTTP_ACCEPT="application/vnd.oai.openapi+json",
        )

        self.assertEqual(response.status_code, 200)
        schema = json.loads(response.content)
        self.assertIn("/api/health/", schema["paths"])
        self.assertIn("/api/auth/register/", schema["paths"])
        self.assertIn("/api/documents/", schema["paths"])
        self.assertIn("get", schema["paths"]["/api/documents/"])
        self.assertIn("post", schema["paths"]["/api/documents/"])
        upload_operation = schema["paths"]["/api/documents/"]["post"]
        self.assertIn(
            "multipart/form-data",
            upload_operation["requestBody"]["content"],
        )
        self.assertEqual(upload_operation["security"], [{"cookieAuth": []}])
        self.assertEqual(schema["components"]["securitySchemes"]["cookieAuth"]["in"], "cookie")

    def test_swagger_ui_is_served(self):
        response = self.client.get("/api/docs/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SwaggerUIBundle")


class RegistrationAPITests(TestCase):
    def test_registration_still_accepts_json_and_creates_user(self):
        response = self.client.post(
            reverse("register"),
            data=json.dumps(
                {
                    "username": "new-user",
                    "email": "new-user@example.com",
                    "password": "a-secure-password",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["message"], "Registracija sėkminga. Galite prisijungti.")
        self.assertTrue(get_user_model().objects.filter(username="new-user").exists())
