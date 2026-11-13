from django.urls import path
from .views import (
    DocumentCollectionView,
    DocumentDetailView,
    DocumentAnalysisView,
    DocumentSummaryPDFView,
    ask_document_question,
    compare_document_versions,
    csrf,
    health,
    login,
    logout,
    preview_document,
    register,
)

urlpatterns = [
    path("health/", health, name="health"),
    path("auth/csrf/", csrf, name="csrf"),
    path("auth/register/", register, name="register"),
    path("auth/login/", login, name="login"),
    path("auth/logout/", logout, name="logout"),
    path("documents/", DocumentCollectionView.as_view(), name="documents"),
    path("documents/<int:document_id>/", DocumentDetailView.as_view(), name="document-detail"),
    path("documents/<int:document_id>/preview/", preview_document, name="document-preview"),
    path("documents/<int:document_id>/analysis/", DocumentAnalysisView.as_view(), name="document-analysis"),
    path("documents/<int:document_id>/summary.pdf", DocumentSummaryPDFView.as_view(), name="document-summary-pdf"),
    path("documents/<int:document_id>/chat/", ask_document_question, name="document-chat"),
    path("documents/compare/", compare_document_versions, name="document-compare"),
]
