import json
from pathlib import Path
from mimetypes import guess_type

from django.core.exceptions import ValidationError
from django.db import DatabaseError
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

from api.models import Document
from api.ai import AIProviderError, get_gemini_provider
from api.rag import DocumentRetrievalError, document_context


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
        "Remkis tik pateiktais dokumento fragmentais. Jei informacijos nepakanka, "
        "aiškiai tai pasakyk ir nesugalvok faktų.\n\n"
        f"Dokumento pavadinimas: {document.original_filename}\n"
        f"Susiję dokumento fragmentai:\n{document_context(document, question)}\n\n"
        f"Naudotojo klausimas: {question}"
    )
    try:
        answer = get_gemini_provider().generate(prompt).strip()
    except (AIProviderError, DocumentRetrievalError, OSError, KeyError, ValueError):
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
    has_differences = report.strip().upper() != "SKIRTUMŲ NĖRA"
    return JsonResponse({"report": report, "has_differences": has_differences})


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
