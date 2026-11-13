import json
import base64
import io
import os
from pathlib import Path
from mimetypes import guess_type

from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.http import FileResponse, HttpResponse, JsonResponse
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.serializers import (
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


class DocumentSerializer(Serializer):
    id = IntegerField()
    title = CharField()
    original_filename = CharField()
    file_size = IntegerField()
    content_type = CharField(allow_blank=True)
    analysis_status = CharField()
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

    prompt = (
        "Atsakyk lietuviškai į naudotojo klausimą apie pasirinktą dokumentą. "
        "Remkis tik pateikta dokumento informacija. Jei informacijos nepakanka, "
        "aiškiai tai pasakyk ir nesugalvok faktų.\n\n"
        f"Dokumento pavadinimas: {document.original_filename}\n"
        f"Dokumento paaiškinimas: {document.simplified_explanation or 'Nėra.'}\n"
        f"Pagrindinės sąlygos: {document.key_conditions or 'Nėra.'}\n\n"
        f"Naudotojo klausimas: {question}"
    )
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
        "Pateik aiškią ataskaitą punktais: kas pridėta, pašalinta arba pakeista. "
        "Jei pateiktos informacijos nepakanka, tai aiškiai nurodyk.\n\n"
        f"Dokumentas: {first.title}\n"
        f"Pirma versija ({first.original_filename}, {first.created_at.isoformat()}):\n"
        f"Paaiškinimas: {first.simplified_explanation or 'Nėra.'}\n"
        f"Sąlygos: {first.key_conditions or 'Nėra.'}\n\n"
        f"Antra versija ({second.original_filename}, {second.created_at.isoformat()}):\n"
        f"Paaiškinimas: {second.simplified_explanation or 'Nėra.'}\n"
        f"Sąlygos: {second.key_conditions or 'Nėra.'}"
    )
    try:
        report = get_gemini_provider().generate(prompt).strip()
    except (AIProviderError, OSError, KeyError, ValueError):
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
