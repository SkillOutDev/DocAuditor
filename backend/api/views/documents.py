import json
import base64
import io
import os
from datetime import datetime
from pathlib import Path
from mimetypes import guess_type

from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.db.models import Q
from django.http import FileResponse, HttpResponse, JsonResponse
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.serializers import (
    BooleanField,
    CharField,
    DictField,
    FileField,
    IntegerField,
    JSONField,
    Serializer,
)
from rest_framework.views import APIView
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from api.models import Document
from api.ai import AIProviderError, get_gemini_provider
from api.analysis import extract_document_text # arba funkcija, kuri jūsų projekte ištraukia tekstą
from api.rag import DocumentRetrievalError, document_context


class DocumentSerializer(Serializer):
    id = IntegerField()
    title = CharField()
    original_filename = CharField()
    file_size = IntegerField()
    content_type = CharField(allow_blank=True)
    analysis_status = CharField()
    simplified_explanation = CharField(allow_blank=True)
    risk_assessment = JSONField()
    created_at = CharField()


class DocumentListResponseSerializer(Serializer):
    documents = DocumentSerializer(many=True)


class DocumentUploadRequestSerializer(Serializer):
    file = FileField(
        help_text="One PDF, DOC, or DOCX file, up to 15 MiB.",
        write_only=True,
    )


class DocumentUploadResponseSerializer(Serializer):
    message = CharField()
    document = DocumentSerializer()


class DocumentErrorResponseSerializer(Serializer):
    message = CharField()
    errors = DictField(child=JSONField(), required=False)


class DocumentQuestionRequestSerializer(Serializer):
    question = CharField(max_length=2000)


class DocumentQuestionResponseSerializer(Serializer):
    answer = CharField()


class DocumentComparisonRequestSerializer(Serializer):
    first_document_id = IntegerField()
    second_document_id = IntegerField()


class DocumentComparisonResponseSerializer(Serializer):
    report = CharField()
    pdf_base64 = CharField()
    pdf_filename = CharField()
    has_differences = BooleanField()


class ManualDocumentAuthenticationPermission(AllowAny):
    """Let the view return its existing 401 response for anonymous requests."""


def _serialize_document(document):
    return {
        "id": document.pk,
        "title": document.title,
        "original_filename": document.original_filename,
        "file_size": document.file_size,
        "content_type": document.content_type,
        "analysis_status": document.analysis_status,
        "simplified_explanation": document.simplified_explanation,
        "risk_assessment": document.risk_assessment,
        "privacy_assessment": document.privacy_assessment,
        "created_at": document.created_at.isoformat(),
    }


def _original_filename(uploaded_file):
    return Path(uploaded_file.name.replace("\\", "/")).name


def preview_document(request, document_id):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"message": "Norėdami peržiūrėti dokumentą, prisijunkite."},
            status=401,
        )

    try:
        document = Document.objects.get(id=document_id, owner=request.user)
    except Document.DoesNotExist:
        return JsonResponse(
            {"message": "Dokumento rasti nepavyko."},
            status=404,
        )

    if not document.file:
        return JsonResponse(
            {"message": "Dokumento turinio peržiūrėti nepavyko."},
            status=404,
        )

    content_type = document.content_type or guess_type(document.original_filename)[0]
    try:
        document_file = document.file.open("rb")
    except OSError:
        return JsonResponse(
            {"message": "Dokumento turinio peržiūrėti nepavyko."},
            status=404,
        )

    response = FileResponse(
        document_file,
        content_type=content_type or "application/octet-stream",
    )
    filename = Path(document.original_filename).name.replace('"', "")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


@extend_schema(
    operation_id="ask_document_question",
    summary="Ask a question about a document",
    request=DocumentQuestionRequestSerializer,
    responses={
        200: DocumentQuestionResponseSerializer,
        400: OpenApiResponse(response=DocumentErrorResponseSerializer),
        401: OpenApiResponse(response=DocumentErrorResponseSerializer),
        404: OpenApiResponse(response=DocumentErrorResponseSerializer),
        502: OpenApiResponse(response=DocumentErrorResponseSerializer),
    },
)
def ask_document_question(request, document_id):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"message": "Norėdami klausti apie dokumentą, prisijunkite."},
            status=401,
        )

    try:
        document = Document.objects.get(id=document_id, owner=request.user)
    except Document.DoesNotExist:
        return JsonResponse({"message": "Dokumento rasti nepavyko."}, status=404)

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        payload = {}
    question = str(payload.get("question", "")).strip()
    if not question:
        return JsonResponse(
            {"message": "Klausimas negali būti tuščias."},
            status=400,
        )

    extracted_text = ""
    if document.file:
        filename_lower = document.original_filename.lower()
        try:
            document.file.open("rb")
            if filename_lower.endswith(".pdf"):
                import pypdf
                reader = pypdf.PdfReader(document.file)
                pages = [page.extract_text() or "" for page in reader.pages]
                extracted_text = "\n".join(pages).strip()
            elif filename_lower.endswith((".docx", ".doc")):
                from docx import Document as WordDocument
                doc = WordDocument(document.file)
                paragraphs = [p.text for p in doc.paragraphs if p.text]
                extracted_text = "\n".join(paragraphs).strip()
        except Exception:
            extracted_text = ""
        finally:
            try:
                document.file.close()
            except Exception:
                pass

    if extracted_text:
        content_context = extracted_text[:40000]  # Paimame iki 40 tūkst. simbolių
    else:
        content_context = (
            f"Dokumento paaiškinimas: {document.simplified_explanation or 'Nėra.'}\n"
            f"Pagrindinės sąlygos: {document.key_conditions or 'Nėra.'}"
        )

    prompt = (
        "Tu esi teisinių dokumentų asistentas. Atsakyk lietuviškai į naudotojo klausimą apie pateiktą dokumentą.\n"
        "Atsakymą formuok TIK remdamasis žemiau pateiktu dokumento turiniu (nebent nurodoma aiškinti savais žodžiais).\n"
        "Būk itin atidus datoms, skaičiams, terminams, kainoms ir sutarties punktams (parašyk kuriame punkte/punktuose tai minima jei įmanoma).\n"
        "Jei pateiktame tekste informacijos apie klausimą tikrai nėra, aiškiai pasakyk: "
        "'Pateiktame dokumente šios informacijos rasti nepavyko.' ir nesugalvok faktų.\n\n"
        f"Dokumento pavadinimas: {document.original_filename}\n"
        f"Dokumento turinys:\n\"\"\"\n{content_context}\n\"\"\"\n\n"
        f"Naudotojo klausimas: {question}\n"
        "Atsakymas:"
    )

    # --- 3. Siunčiame užklausą į Gemini ---
    try:
        answer = get_gemini_provider().generate(prompt).strip()
    except (AIProviderError, OSError, KeyError, ValueError):
        return JsonResponse({"message": "Nepavyko sukurti pokalbio."}, status=502)

    if not answer:
        return JsonResponse({"message": "Nepavyko sukurti pokalbio."}, status=502)

    return JsonResponse({"answer": answer})


@extend_schema(
    operation_id="compare_document_versions",
    summary="Compare two versions of a document",
    request=DocumentComparisonRequestSerializer,
    responses={
        200: DocumentComparisonResponseSerializer,
        400: OpenApiResponse(response=DocumentErrorResponseSerializer),
        401: OpenApiResponse(response=DocumentErrorResponseSerializer),
        404: OpenApiResponse(response=DocumentErrorResponseSerializer),
        502: OpenApiResponse(response=DocumentErrorResponseSerializer),
    },
)
def compare_document_versions(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"message": "Norėdami lyginti dokumentus, prisijunkite."},
            status=401,
        )

    try:
        payload = json.loads(request.body or "{}")
        first_id = int(payload.get("first_document_id"))
        second_id = int(payload.get("second_document_id"))
    except (TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse(
            {"message": "Nepasirinkti dokumentai palyginimui"},
            status=400,
        )

    if first_id == second_id:
        return JsonResponse(
            {"message": "Nepasirinkti dokumentai palyginimui"},
            status=400,
        )

    documents = list(
        Document.objects.filter(
            owner=request.user,
            id__in=(first_id, second_id),
        )
    )
    if len(documents) != 2 or documents[0].title != documents[1].title:
        return JsonResponse(
            {"message": "Dokumentų palyginti nepavyko"},
            status=400,
        )

    first = next(document for document in documents if document.id == first_id)
    second = next(document for document in documents if document.id == second_id)
    prompt = (
        "Atsakyk lietuviškai ir palygink dvi to paties dokumento versijas. "
        "Naudok tik pateiktą informaciją ir pateik ataskaitą tiksliai trimis "
        "atskiromis antraštėmis: PRIDĖTA, PAŠALINTA, PAKEISTA. "
        "Kiekvienos antraštės skirtumus pateik sunumeruotu sąrašu, naudojant "
        "formatą '1. ...', '2. ...'; nenaudok brūkšnelių ar kitų sąrašo žymenų. "
        "Versijų pavadinimai jau pateikti žemiau, todėl nekartok dokumento "
        "pavadinimo prie kiekvieno punkto. Jei skirtumų nėra, atsakyk tiksliai "
        "'SKIRTUMŲ NĖRA'. Jei informacijos nepakanka, aiškiai tai nurodyk.\n\n"
        f"Dokumentas: {first.title}\n"
        f"Pirma versija ({first.original_filename}, {first.created_at.isoformat()}):\n"
        f"Atitinkami pirmos versijos fragmentai:\n{document_context(first, limit=12)}\n\n"
        f"Antra versija ({second.original_filename}, {second.created_at.isoformat()}):\n"
        f"Atitinkami antros versijos fragmentai:\n{document_context(second, limit=12)}"
    )
    try:
        report = get_gemini_provider().generate(prompt).strip()
    except (AIProviderError, DocumentRetrievalError, OSError, KeyError, ValueError):
        return JsonResponse(
            {"message": "Dokumentų palyginti nepavyko"},
            status=502,
        )

    if not report:
        return JsonResponse(
            {"message": "Dokumentų palyginti nepavyko"},
            status=502,
        )
    try:
        pdf_content = _build_comparison_pdf(report, first, second)
    except (OSError, ValueError):
        return JsonResponse(
            {"message": "Dokumentų palyginti nepavyko"},
            status=502,
        )
    return JsonResponse(
        {
            "report": report,
            "pdf_base64": base64.b64encode(pdf_content).decode("ascii"),
            "pdf_filename": f"{Path(first.original_filename).stem}-palyginimas.pdf",
            "has_differences": report.strip().upper() != "SKIRTUMŲ NĖRA",
        }
    )


def _register_pdf_font():
    font_name = "DocAuditorPdfFont"
    if font_name in pdfmetrics.getRegisteredFontNames():
        return font_name

    candidates = [
        os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "arial.ttf"),
        r"C:\Windows\Fonts\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.isfile(path):
            pdfmetrics.registerFont(TTFont(font_name, path))
            return font_name
    return "Helvetica"


def _build_comparison_pdf(report, first, second):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    font_name = _register_pdf_font()
    pdf.setTitle(f"{first.title} - dokumento versijų palyginimas")
    pdf.setFont(font_name, 16)
    pdf.drawString(48, height - 52, "Dokumento versijų palyginimas")
    pdf.setFont(font_name, 10)
    pdf.drawString(48, height - 72, f"Dokumentas: {first.title}")
    pdf.drawString(48, height - 88, f"Versijos: {first.original_filename} ir {second.original_filename}")

    text = pdf.beginText(48, height - 120)
    text.setFont(font_name, 10)
    text.setLeading(14)
    for paragraph in report.splitlines() or [""]:
        words = paragraph.split()
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if pdf.stringWidth(candidate, font_name, 10) > width - 96 and line:
                text.textLine(line)
                line = word
            else:
                line = candidate
        text.textLine(line)
        if text.getY() < 48:
            pdf.drawText(text)
            pdf.showPage()
            pdf.setFont(font_name, 10)
            text = pdf.beginText(48, height - 48)
            text.setLeading(14)
    pdf.drawText(text)
    pdf.save()
    return buffer.getvalue()


class DocumentCollectionView(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [ManualDocumentAuthenticationPermission]

    @extend_schema(
        operation_id="list_documents",
        summary="List the current user's documents",
        responses={
            200: DocumentListResponseSerializer,
            401: OpenApiResponse(
                response=DocumentErrorResponseSerializer,
                description="Authentication is required.",
            ),
        },
    )
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"message": "Norėdami tvarkyti dokumentus, prisijunkite."},
                status=401,
            )

        user_documents = Document.objects.filter(owner=request.user)
        title_filter = (request.GET.get("title") or "").strip()
        date_filter = (request.GET.get("date") or "").strip()
        type_filter = (request.GET.get("type") or "").strip().lower()

        if title_filter:
            title_lookup = title_filter.lower()
            user_documents = user_documents.filter(
                Q(title__icontains=title_lookup) | Q(original_filename__icontains=title_lookup)
            )

        if date_filter:
            try:
                datetime.strptime(date_filter, "%Y-%m-%d")
            except ValueError:
                user_documents = user_documents.none()
            else:
                user_documents = user_documents.filter(created_at__date=date_filter)

        if type_filter:
            normalized_type = {
                "pdf": ".pdf",
                "doc": ".doc",
                "docx": ".docx",
            }.get(type_filter)
            if normalized_type:
                user_documents = user_documents.filter(original_filename__iendswith=normalized_type)
            else:
                user_documents = user_documents.filter(
                    Q(content_type__icontains=type_filter) | Q(original_filename__icontains=type_filter)
                )

        return JsonResponse(
            {"documents": [_serialize_document(document) for document in user_documents]}
        )

    @extend_schema(
        operation_id="upload_document",
        summary="Upload and save a document",
        request=DocumentUploadRequestSerializer,
        responses={
            201: DocumentUploadResponseSerializer,
            400: OpenApiResponse(
                response=DocumentErrorResponseSerializer,
                description="Missing file or unsupported file type/size.",
            ),
            401: OpenApiResponse(
                response=DocumentErrorResponseSerializer,
                description="Authentication is required.",
            ),
        },
    )
    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"message": "Norėdami tvarkyti dokumentus, prisijunkite."},
                status=401,
            )

        uploaded_files = request.FILES.getlist("file")
        if len(uploaded_files) != 1:
            return JsonResponse(
                {
                    "message": "Nepavyko įkelti dokumento.",
                    "errors": {"file": "Pasirinkite vieną dokumentą."},
                },
                status=400,
            )

        uploaded_file = uploaded_files[0]
        original_filename = _original_filename(uploaded_file)
        title = Path(original_filename).stem.strip()[:255] or "Dokumentas"
        document = Document(
            owner=request.user,
            title=title,
            file=uploaded_file,
            original_filename=original_filename[:255],
            file_size=uploaded_file.size,
            content_type=uploaded_file.content_type or "",
        )
        try:
            document.full_clean()
            document.save()
        except ValidationError as error:
            return JsonResponse(
                {
                    "message": "Nepavyko įkelti dokumento.",
                    "errors": {"file": error.messages},
                },
                status=400,
            )

        return JsonResponse(
            {
                "message": "Dokumentas išsaugotas sėkmingai",
                "document": _serialize_document(document),
            },
            status=201,
        )


class DocumentDetailView(APIView):
    permission_classes = [ManualDocumentAuthenticationPermission]

    @extend_schema(
        operation_id="delete_document",
        summary="Delete the current user's document",
        responses={
            204: OpenApiResponse(description="Document deleted successfully."),
            401: OpenApiResponse(
                response=DocumentErrorResponseSerializer,
                description="Authentication is required.",
            ),
            404: OpenApiResponse(
                response=DocumentErrorResponseSerializer,
                description="Document was not found.",
            ),
            500: OpenApiResponse(
                response=DocumentErrorResponseSerializer,
                description="Document could not be deleted.",
            ),
        },
    )
    def delete(self, request, document_id):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"message": "Norėdami tvarkyti dokumentus, prisijunkite."},
                status=401,
            )

        try:
            document = Document.objects.get(id=document_id, owner=request.user)
        except Document.DoesNotExist:
            return JsonResponse(
                {"message": "Dokumento rasti nepavyko."},
                status=404,
            )

        try:
            if document.file:
                document.file.delete(save=False)
            document.delete()
        except (OSError, DatabaseError):
            return JsonResponse(
                {"message": "Dokumento ištrinti nepavyko."},
                status=500,
            )

        return HttpResponse(status=204)
