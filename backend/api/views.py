import json
from json import JSONDecodeError

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


def health(request):
    return JsonResponse({"status": "ok", "service": "docauditor-api"})


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
