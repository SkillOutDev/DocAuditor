from pathlib import Path
from mimetypes import guess_type

from django.core.exceptions import ValidationError
from django.http import FileResponse, JsonResponse
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

from api.models import Document


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
