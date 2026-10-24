import os
import sys

import coverage

cov = coverage.Coverage(source=["api", "config"], omit=["*/migrations/*"])
cov.start()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
from django.conf import settings

settings.DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
django.setup()
from django.core.management import call_command

try:
    call_command("test", "api")
finally:
    cov.stop()
    cov.save()
    cov.report(show_missing=True)
    sys.stdout.flush()
