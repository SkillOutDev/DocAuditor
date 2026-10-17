import json
from json import JSONDecodeError

from django.contrib.auth import authenticate, get_user_model, login as auth_login, logout as auth_logout
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.serializers import CharField, DictField, Serializer

INVALID_CREDENTIALS_MESSAGE = "Neteisingai suvesti prisijungimo duomenys"


class LoginRequestSerializer(Serializer):
    email = CharField(max_length=254)
    password = CharField(max_length=128, write_only=True)


class LoginUserSerializer(Serializer):
    username = CharField()
    email = CharField()


class LoginResponseSerializer(Serializer):
    message = CharField()
    user = LoginUserSerializer()


class LoginErrorSerializer(Serializer):
    message = CharField()


class LogoutResponseSerializer(Serializer):
    message = CharField()


class RegisterRequestSerializer(Serializer):
    username = CharField(max_length=150)
    email = CharField(max_length=254)
    password = CharField(min_length=8, max_length=128, write_only=True)


class RegisterResponseSerializer(Serializer):
    message = CharField()


class RegisterErrorSerializer(Serializer):
    errors = DictField(child=CharField())


@extend_schema(
    operation_id="register",
    summary="Register a user",
    request=RegisterRequestSerializer,
    responses={
        201: RegisterResponseSerializer,
        400: OpenApiResponse(
            response=RegisterErrorSerializer,
            description="Invalid request or field values.",
        ),
        409: OpenApiResponse(
            response=RegisterErrorSerializer,
            description="Username or email is already in use.",
        ),
    },
    auth=[],
)
@api_view(["POST"])
@csrf_exempt
@require_POST
def register(request):
    try:
        data = json.loads(request.body)
    except (JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"errors": {"form": "Netinkamas užklausos formatas."}},
            status=400,
        )

    if not isinstance(data, dict):
        return JsonResponse(
            {"errors": {"form": "Netinkamas užklausos formatas."}},
            status=400,
        )

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    errors = {}

    if not isinstance(username, str) or not username.strip():
        errors["username"] = "Įveskite vartotojo vardą."
    elif len(username.strip()) > 150:
        errors["username"] = "Vartotojo vardas negali viršyti 150 simbolių."
    if not isinstance(email, str):
        errors["email"] = "Įveskite galiojantį el. pašto adresą."
    else:
        email = email.strip().lower()
        if len(email) > 254:
            errors["email"] = "Įveskite galiojantį el. pašto adresą."
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors["email"] = "Įveskite galiojantį el. pašto adresą."
    if not isinstance(password, str) or len(password) < 8 or len(password) > 128:
        errors["password"] = "Slaptažodį turi sudaryti 8–128 simboliai."
    if errors:
        return JsonResponse({"errors": errors}, status=400)

    username = username.strip()
    User = get_user_model()
    try:
        User._meta.get_field("username").run_validators(username)
    except ValidationError:
        return JsonResponse(
            {"errors": {"username": "Vartotojo vardas turi netinkamų simbolių."}},
            status=400,
        )
    if User.objects.filter(username__iexact=username).exists():
        return JsonResponse(
            {"errors": {"username": "Šis vartotojo vardas jau naudojamas."}},
            status=409,
        )
    if User.objects.filter(email__iexact=email).exists():
        return JsonResponse(
            {"errors": {"email": "Šis el. pašto adresas jau užregistruotas."}},
            status=409,
        )

    try:
        with transaction.atomic():
            User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )
    except IntegrityError:
        return JsonResponse(
            {"errors": {"username": "Šis vartotojo vardas jau naudojamas."}},
            status=409,
        )

    return JsonResponse(
        {"message": "Registracija sėkminga. Galite prisijungti."},
        status=201,
    )


@ensure_csrf_cookie
@require_GET
def csrf(request):
    return JsonResponse({"message": "CSRF slapukas nustatytas."})


def _invalid_credentials():
    return JsonResponse({"message": INVALID_CREDENTIALS_MESSAGE}, status=401)


@extend_schema(
    operation_id="login",
    summary="Log in with email and password",
    request=LoginRequestSerializer,
    responses={
        200: LoginResponseSerializer,
        401: OpenApiResponse(
            response=LoginErrorSerializer,
            description="Incorrect email or password.",
        ),
    },
    auth=[],
)
@api_view(["POST"])
@authentication_classes([])
def login(request):
    try:
        data = json.loads(request.body)
    except (JSONDecodeError, UnicodeDecodeError):
        return _invalid_credentials()

    email = data.get("email") if isinstance(data, dict) else None
    password = data.get("password") if isinstance(data, dict) else None
    if not isinstance(email, str) or not isinstance(password, str):
        return _invalid_credentials()
    email = email.strip()
    if not email or not password or len(email) > 254 or len(password) > 128:
        return _invalid_credentials()

    User = get_user_model()
    candidates = list(User.objects.filter(email__iexact=email)[:5])
    if not candidates:
        # Spend comparable time hashing so unknown emails are not distinguishable.
        User().set_password(password)
        return _invalid_credentials()

    for candidate in candidates:
        user = authenticate(
            request._request, username=candidate.get_username(), password=password
        )
        if user is not None:
            auth_login(request._request, user)
            return JsonResponse(
                {
                    "message": "Prisijungta sėkmingai.",
                    "user": {"username": user.get_username(), "email": user.email},
                }
            )

    return _invalid_credentials()


@extend_schema(
    operation_id="logout",
    summary="Log out the current user",
    request=None,
    responses={200: LogoutResponseSerializer},
    auth=[],
)
@api_view(["POST"])
@authentication_classes([])
def logout(request):
    auth_logout(request._request)
    return JsonResponse({"message": "Atsijungta sėkmingai."})
