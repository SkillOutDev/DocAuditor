import logging
import json
from io import BytesIO

from django.http import FileResponse, JsonResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.serializers import CharField, JSONField, Serializer
from rest_framework.views import APIView

from api.analysis import (
    OLLAMA_MAX_SUMMARY_LENGTH,
    AnalysisError,
    create_summary_pdf,
    extract_document_text,
    generate_summary,
    generate_risk_assessment,
    generate_privacy_assessment,
)
from api.models import Document
from api.views.documents import DocumentErrorResponseSerializer, ManualDocumentAuthenticationPermission

logger = logging.getLogger(__name__)
FAILURE_MESSAGE = "Analizė nepavyko, bandykite dar kartą"


class AnalysisResponseSerializer(Serializer):
    summary = CharField(
        max_length=OLLAMA_MAX_SUMMARY_LENGTH,
        help_text="Gemini summaries are limited to 700 characters; Ollama summaries to 2000.",
    )
    risks = JSONField()
    privacy = JSONField()


class SaveAnalysisRequestSerializer(Serializer):
    summary = CharField(
        max_length=OLLAMA_MAX_SUMMARY_LENGTH,
        allow_blank=False,
    )
    risks = JSONField(required=False, default=list)
    privacy = JSONField(required=False, default=dict)


class SaveAnalysisResponseSerializer(Serializer):
    message = CharField()
    summary = CharField(max_length=OLLAMA_MAX_SUMMARY_LENGTH)
    risks = JSONField()
    privacy = JSONField()


class DocumentAnalysisView(APIView):
    permission_classes = [ManualDocumentAuthenticationPermission]

    @extend_schema(
        operation_id="analyze_document",
        summary="Analyze a document using Gemini, with Ollama as fallback",
        request=None,
        responses={200: AnalysisResponseSerializer, 400: DocumentErrorResponseSerializer,
                   401: DocumentErrorResponseSerializer, 404: DocumentErrorResponseSerializer,
                   502: DocumentErrorResponseSerializer},
    )
    def post(self, request, document_id):
        if not request.user.is_authenticated:
            return JsonResponse({"message": "Norėdami analizuoti dokumentą, prisijunkite."}, status=401)
        document = Document.objects.filter(pk=document_id, owner=request.user).first()
        if document is None:
            return JsonResponse({"message": "Dokumento rasti nepavyko."}, status=404)
        try:
            text = extract_document_text(document)
        except AnalysisError as error:
            logger.warning("Document text extraction failed (%s)", type(error).__name__)
            return JsonResponse({"message": FAILURE_MESSAGE}, status=400)
        try:
            summary = generate_summary(text)
        except AnalysisError:
            return JsonResponse({"message": FAILURE_MESSAGE}, status=502)
        try:
            risks = generate_risk_assessment(text)
        except AnalysisError:
            return JsonResponse(
                {"message": "Nepavyko atlikti rizikų vertinimo, bandykite analizuoti iš naujo"},
                status=502,
            )
        try:
            privacy = generate_privacy_assessment(text)
        except AnalysisError:
            return JsonResponse(
                {"message": "Nepavyko išanalizuoti asmens duomenų sąlygų"},
                status=502,
            )
        return JsonResponse({"summary": summary, "risks": risks, "privacy": privacy})


class DocumentAnalysisSaveView(APIView):
    permission_classes = [ManualDocumentAuthenticationPermission]

    @extend_schema(
        operation_id="save_document_analysis",
        summary="Save a generated document analysis",
        request=SaveAnalysisRequestSerializer,
        responses={200: SaveAnalysisResponseSerializer,
                   400: DocumentErrorResponseSerializer,
                   401: DocumentErrorResponseSerializer,
                   404: DocumentErrorResponseSerializer},
    )
    def post(self, request, document_id):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"message": "Norėdami išsaugoti analizę, prisijunkite."},
                status=401,
            )
        document = Document.objects.filter(pk=document_id, owner=request.user).first()
        if document is None:
            return JsonResponse({"message": "Dokumento rasti nepavyko."}, status=404)
        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            payload = {}
        summary = payload.get("summary")
        risks = payload.get("risks", [])
        privacy = payload.get("privacy", {})
        if not isinstance(summary, str) or not summary.strip():
            return JsonResponse(
                {"message": "Analizės išsaugoti nepavyko.", "errors": {"summary": "Santrauka negali būti tuščia."}},
                status=400,
            )
        summary = summary.strip()
        if len(summary) > OLLAMA_MAX_SUMMARY_LENGTH:
            return JsonResponse(
                {"message": "Analizės išsaugoti nepavyko.", "errors": {"summary": "Santrauka per ilga."}},
                status=400,
            )
        if not isinstance(risks, list):
            return JsonResponse(
                {"message": "Analizės išsaugoti nepavyko.", "errors": {"risks": "Netinkamas rizikų formatas."}},
                status=400,
            )
        if not isinstance(privacy, dict):
            return JsonResponse(
                {"message": "Analizės išsaugoti nepavyko.", "errors": {"privacy": "Netinkamas privatumo formato duomenys."}},
                status=400,
            )
        document.simplified_explanation = summary
        document.risk_assessment = risks
        document.privacy_assessment = privacy
        document.analysis_status = Document.AnalysisStatus.COMPLETED
        document.analysis_error = ""
        document.save(update_fields=[
            "simplified_explanation",
            "risk_assessment",
            "privacy_assessment",
            "analysis_status",
            "analysis_error",
            "updated_at",
        ])
        return JsonResponse({
            "message": "Analizė sėkmingai išsaugota",
            "summary": summary,
            "risks": risks,
            "privacy": privacy,
        })


class DocumentSummaryPDFView(APIView):
    permission_classes = [ManualDocumentAuthenticationPermission]

    @extend_schema(
        operation_id="download_document_summary",
        summary="Download the document analysis as PDF",
        responses={(200, "application/pdf"): OpenApiTypes.BINARY,
                   401: DocumentErrorResponseSerializer, 404: DocumentErrorResponseSerializer,
                   500: DocumentErrorResponseSerializer},
    )
    def get(self, request, document_id):
        if not request.user.is_authenticated:
            return JsonResponse({"message": "Norėdami atsisiųsti santrauką, prisijunkite."}, status=401)
        document = Document.objects.filter(pk=document_id, owner=request.user).first()
        if document is None or not document.simplified_explanation:
            return JsonResponse({"message": "Santraukos rasti nepavyko."}, status=404)
        output = BytesIO()
        try:
            create_summary_pdf(
                document.simplified_explanation,
                output,
                document.risk_assessment,
                document.privacy_assessment,
            )
        except (AnalysisError, OSError, ValueError) as error:
            logger.error("Summary PDF generation failed (%s)", type(error).__name__)
            return JsonResponse({"message": "Nepavyko sukurti santraukos."}, status=500)
        output.seek(0)
        return FileResponse(output, as_attachment=True, filename="santrauka.pdf", content_type="application/pdf")
