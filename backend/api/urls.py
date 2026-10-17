from django.urls import path
from .views import DocumentCollectionView, csrf, health, login, logout, register

urlpatterns = [
    path("health/", health, name="health"),
    path("auth/csrf/", csrf, name="csrf"),
    path("auth/register/", register, name="register"),
    path("auth/login/", login, name="login"),
    path("auth/logout/", logout, name="logout"),
    path("documents/", DocumentCollectionView.as_view(), name="documents"),
]
