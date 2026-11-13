import httpx
from django.core.management.base import BaseCommand, CommandError
from google.genai.errors import APIError

from api.ai import GeminiProvider, MissingGeminiAPIKey


class Command(BaseCommand):
    help = "Check Gemini connectivity and list models available to the configured key."

    def add_arguments(self, parser):
        parser.add_argument(
            "--generate",
            action="store_true",
            help="Also test the configured model using a short sample prompt.",
        )

    def handle(self, *args, **options):
        try:
            provider = GeminiProvider()
            self.stdout.write(f"Configured model: {provider.model}")
            self.stdout.write("Fetching available models:")
            count = 0
            for model in provider.client.models.list():
                self.stdout.write(f" - {model.name}")
                count += 1
            self.stdout.write(self.style.SUCCESS(f"Gemini model listing succeeded ({count} models)."))
            if options["generate"]:
                response = provider.generate("Say hello in one word.")
                if not response.strip():
                    raise CommandError("Gemini returned an empty generation response.")
                self.stdout.write(self.style.SUCCESS("Gemini generation succeeded."))
        except MissingGeminiAPIKey as error:
            raise CommandError("GEMINI_API_KEY is missing or empty; set it in backend/.env.") from error
        except APIError as error:
            code = error.code if isinstance(error.code, int) else "unknown"
            raise CommandError(f"Gemini API request failed (HTTP {code}). Check the key, model and account.") from error
        except (httpx.HTTPError, OSError, TimeoutError) as error:
            raise CommandError(f"Gemini connection failed ({type(error).__name__}).") from error
