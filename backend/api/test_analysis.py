import json
import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch

import requests
from docx import Document as WordDocument
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from pypdf import PdfReader
from reportlab.pdfgen import canvas

from api.ai import MissingGeminiAPIKey
from api.analysis import AnalysisError, extract_document_text, generate_summary
from api.models import Document


class AnalysisTests(TestCase):
    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        override = override_settings(MEDIA_ROOT=self.media.name)
        override.enable()
        self.addCleanup(override.disable)
        self.owner = get_user_model().objects.create_user(username="owner", password="test-pass")
        self.other = get_user_model().objects.create_user(username="other", password="test-pass")
        self.document = Document.objects.create(
            owner=self.owner, title="Contract", original_filename="contract.pdf",
            file=SimpleUploadedFile("contract.pdf", b"not a pdf"), file_size=9,
        )
        self.url = reverse("document-analysis", args=[self.document.pk])
        self.save_url = reverse("document-analysis-save", args=[self.document.pk])
        self.pdf_url = reverse("document-summary-pdf", args=[self.document.pk])

    def test_analysis_and_download_require_owner(self):
        self.assertEqual(self.client.post(self.url).status_code, 401)
        self.assertEqual(self.client.post(self.save_url).status_code, 401)
        self.assertEqual(self.client.get(self.pdf_url).status_code, 401)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.save_url).status_code, 404)
        self.assertEqual(self.client.get(self.pdf_url).status_code, 404)

    def test_analysis_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        self.assertEqual(client.post(self.url).status_code, 403)
        token = client.get(reverse("csrf")).cookies["csrftoken"].value
        with patch("api.views.analysis.extract_document_text", return_value="Sąlygos"), \
             patch("api.views.analysis.generate_summary", return_value="Santrauka"), \
             patch("api.views.analysis.generate_risk_assessment", return_value=[]):
            self.assertEqual(client.post(self.url, HTTP_X_CSRFTOKEN=token).status_code, 200)

    def test_summary_is_only_saved_after_explicit_save_and_downloaded_as_readable_pdf(self):
        self.client.force_login(self.owner)
        risks = [{
            "level": "high",
            "category": "Mokėjimai",
            "explanation": "Klientui gali tekti mokėti papildomus mokesčius.",
            "clause": "5.2 punktas",
        }]
        with patch("api.views.analysis.extract_document_text", return_value="Sąlygos"), \
             patch("api.views.analysis.generate_summary", return_value="Sąlygos: įmoka ąčęėįšųūž."), \
             patch("api.views.analysis.generate_risk_assessment", return_value=risks):
            response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"summary": "Sąlygos: įmoka ąčęėįšųūž.", "risks": risks})
        self.document.refresh_from_db()
        self.assertEqual(self.document.simplified_explanation, "")
        self.assertEqual(self.client.get(self.pdf_url).status_code, 404)
        response = self.client.post(self.save_url, data=json.dumps(response.json()), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Analizė sėkmingai išsaugota")
        self.document.refresh_from_db()
        self.assertEqual(self.document.analysis_status, Document.AnalysisStatus.COMPLETED)
        self.assertEqual(self.document.simplified_explanation, "Sąlygos: įmoka ąčęėįšųūž.")
        self.assertEqual(self.document.risk_assessment, risks)
        listed = self.client.get(reverse("documents")).json()["documents"][0]
        self.assertEqual(listed["simplified_explanation"], self.document.simplified_explanation)
        response = self.client.get(self.pdf_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        reader = PdfReader(BytesIO(b"".join(response.streaming_content)))
        self.assertIn("Sąlygos: įmoka ąčęėįšųūž.", reader.pages[0].extract_text())
        pdf_text = reader.pages[0].extract_text()
        self.assertIn("Nustatytos rizikos ir grėsmės", pdf_text)
        self.assertIn("Didelė rizika", pdf_text)
        self.assertIn("5.2 punktas", pdf_text)

    def test_failure_does_not_destroy_previous_summary(self):
        self.document.simplified_explanation = "Ankstesnė santrauka"
        self.document.save()
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(self.url).status_code, 400)
        self.document.refresh_from_db()
        self.assertEqual(self.document.simplified_explanation, "Ankstesnė santrauka")
        with patch("api.views.analysis.extract_document_text", return_value="Sąlygos"), \
             patch("api.views.analysis.generate_summary", side_effect=AnalysisError):
            response = self.client.post(self.url)
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["message"], "Analizė nepavyko, bandykite dar kartą")

    def test_risk_assessment_failure_has_specific_message(self):
        self.client.force_login(self.owner)
        with patch("api.views.analysis.extract_document_text", return_value="Sąlygos"), \
             patch("api.views.analysis.generate_summary", return_value="Santrauka"), \
             patch("api.views.analysis.generate_risk_assessment", side_effect=AnalysisError):
            response = self.client.post(self.url)
        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json()["message"],
            "Nepavyko atlikti rizikų vertinimo, bandykite analizuoti iš naujo",
        )

    def test_download_requires_summary(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.pdf_url).status_code, 404)

    def test_long_ollama_summary_is_saved_and_downloadable_after_explicit_save(self):
        self.client.force_login(self.owner)
        summary = "Sąlygos ir mokėjimas. " * 90
        self.assertTrue(700 < len(summary.strip()) <= 2000)
        ollama = Mock()
        ollama.generate.return_value = summary
        with patch("api.views.analysis.extract_document_text", return_value="Sąlygos"), \
             patch("api.analysis.get_gemini_provider", side_effect=MissingGeminiAPIKey), \
             patch("api.analysis.OllamaProvider", return_value=ollama), \
             patch("api.views.analysis.generate_risk_assessment", return_value=[]):
            response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["summary"], summary.strip())
        self.document.refresh_from_db()
        self.assertEqual(self.document.simplified_explanation, "")
        self.client.post(
            self.save_url,
            data=json.dumps(response.json()),
            content_type="application/json",
        )
        self.document.refresh_from_db()
        self.assertEqual(self.document.simplified_explanation, summary.strip())
        response = self.client.get(self.pdf_url)
        self.assertEqual(response.status_code, 200)
        reader = PdfReader(BytesIO(b"".join(response.streaming_content)))
        self.assertIn("Sąlygos ir mokėjimas.", reader.pages[0].extract_text())

    def test_save_requires_a_non_empty_summary(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            self.save_url,
            data=json.dumps({"summary": " "}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.document.refresh_from_db()
        self.assertEqual(self.document.simplified_explanation, "")

    def test_api_schema_documents_analysis_and_pdf(self):
        response = self.client.get("/api/schema/", HTTP_ACCEPT="application/vnd.oai.openapi+json")
        paths = json.loads(response.content)["paths"]
        self.assertIn("post", paths["/api/documents/{document_id}/analysis/"])
        pdf = paths["/api/documents/{document_id}/summary.pdf"]["get"]["responses"]["200"]
        self.assertIn("application/pdf", pdf["content"])
        schema = json.loads(response.content)
        summary = schema["components"]["schemas"]["AnalysisResponse"]["properties"]["summary"]
        self.assertEqual(summary["maxLength"], 2000)

    def test_extract_real_pdf_and_docx(self):
        pdf = BytesIO()
        page = canvas.Canvas(pdf)
        page.drawString(50, 750, "Contract terms")
        page.save()
        word = WordDocument()
        word.add_paragraph("Pagrindinės sąlygos")
        table = word.add_table(rows=1, cols=1)
        table.cell(0, 0).text = "Mokėjimas"
        docx = BytesIO()
        word.save(docx)
        for name, content, expected in [
            ("contract.pdf", pdf.getvalue(), "Contract terms"),
            ("contract.docx", docx.getvalue(), "Pagrindinės sąlygos\nMokėjimas"),
        ]:
            with self.subTest(name=name):
                document = Document(
                    owner=self.owner, original_filename=name,
                    file=SimpleUploadedFile(name, content),
                )
                self.assertIn(expected, extract_document_text(document))

    def test_legacy_doc_uses_local_reader_and_failure_is_explicit(self):
        document = Document(owner=self.owner, original_filename="x.doc",
                            file=SimpleUploadedFile("x.doc", b"doc"))
        def fake_run(args, **kwargs):
            Path(args[-1]).with_suffix(".txt").write_text("Sąlygos", encoding="utf-8")
        with patch("api.analysis.subprocess.run", side_effect=fake_run) as run:
            self.assertEqual(extract_document_text(document), "Sąlygos")
            self.assertIn("--headless", run.call_args.args[0])
        with patch("api.analysis.subprocess.run", side_effect=FileNotFoundError):
            with self.assertRaises(AnalysisError):
                extract_document_text(document)

    def test_provider_order_fallback_and_length_limit(self):
        gemini = Mock()
        ollama = Mock()
        gemini.generate.return_value = "G" * 700
        ollama.generate.return_value = "Atsarginė santrauka"
        with patch("api.analysis.get_gemini_provider", return_value=gemini), \
             patch("api.analysis.OllamaProvider", return_value=ollama) as ollama_factory:
            self.assertEqual(len(generate_summary("document")), 700)
            ollama_factory.assert_not_called()
            gemini.generate.return_value = "G" * 701
            self.assertEqual(generate_summary("document"), "Atsarginė santrauka")
            gemini.generate.side_effect = requests.ConnectionError()
            self.assertEqual(generate_summary("document"), "Atsarginė santrauka")
            ollama.generate.return_value = ""
            with self.assertRaises(AnalysisError):
                generate_summary("document")
