from django.urls import path
from .views import DocumentCollectionView, csrf, health, login, logout, preview_document, register

urlpatterns = [
    path("health/", health, name="health"),
    path("auth/csrf/", csrf, name="csrf"),
    path("auth/register/", register, name="register"),
    path("auth/login/", login, name="login"),
    path("auth/logout/", logout, name="logout"),
    path("documents/", DocumentCollectionView.as_view(), name="documents"),
    path("documents/<int:document_id>/preview/", preview_document, name="document-preview"),
]
