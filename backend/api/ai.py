import os
from typing import Protocol

import requests


class AIProvider(Protocol):
    def generate(self, prompt: str) -> str: ...


class GeminiProvider:
    def __init__(self):
        from google import genai

        self.client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    def generate(self, prompt: str) -> str:
        response = self.client.models.generate_content(model=self.model, contents=prompt)
        return response.text or ""


class OllamaProvider:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2")

    def generate(self, prompt: str) -> str:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["response"]


def get_ai_provider() -> AIProvider:
    provider = os.getenv("AI_PROVIDER", "ollama").lower()
    if provider == "gemini":
        return GeminiProvider()
    if provider == "ollama":
        return OllamaProvider()
    raise ValueError(f"Unsupported AI_PROVIDER: {provider}")

