from django.urls import path
from .views import DocumentCollectionView, health, register

urlpatterns = [
    path("health/", health, name="health"),
    path("auth/register/", register, name="register"),
    path("documents/", DocumentCollectionView.as_view(), name="documents"),
]
