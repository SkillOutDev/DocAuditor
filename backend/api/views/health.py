from django.http import JsonResponse
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.serializers import CharField, Serializer


class HealthResponseSerializer(Serializer):
    status = CharField()
    service = CharField()


@extend_schema(
    operation_id="health_check",
    summary="Check API health",
    responses=HealthResponseSerializer,
    auth=[],
)
@api_view(["GET"])
def health(request):
    return JsonResponse({"status": "ok", "service": "docauditor-api"})
