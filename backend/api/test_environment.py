import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from django.test import SimpleTestCase


class EnvironmentSettingsTests(SimpleTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        config = self.root / "config"
        config.mkdir()
        shutil.copyfile(Path(__file__).resolve().parents[1] / "config" / "settings.py", config / "settings.py")
        self.settings_path = config / "settings.py"

    def load_settings(self, overrides=None):
        env = os.environ.copy()
        for key in ("GEMINI_API_KEY", "OLLAMA_MODEL", "POSTGRES_DB"):
            env.pop(key, None)
        env.update(overrides or {})
        script = (
            "import json, os, runpy, sys; "
            "settings = runpy.run_path(sys.argv[1]); "
            "print(json.dumps([os.getenv('GEMINI_API_KEY'), os.getenv('OLLAMA_MODEL'), "
            "settings['DATABASES']['default']['NAME']]))"
        )
        result = subprocess.run(
            [sys.executable, "-c", script, str(self.settings_path)],
            env=env, cwd=self.root, capture_output=True, text=True, check=True,
        )
        return json.loads(result.stdout)

    def test_loads_env_before_django_settings(self):
        (self.root / ".env").write_text(
            "GEMINI_API_KEY=test-key\nOLLAMA_MODEL=example-model\nPOSTGRES_DB=example-db\n",
            encoding="utf-8",
        )
        self.assertEqual(self.load_settings(), ["test-key", "example-model", "example-db"])

    def test_existing_environment_takes_precedence(self):
        (self.root / ".env").write_text(
            "OLLAMA_MODEL=file-model\nPOSTGRES_DB=file-db\n", encoding="utf-8",
        )
        self.assertEqual(
            self.load_settings({"OLLAMA_MODEL": "process-model", "POSTGRES_DB": "process-db"}),
            [None, "process-model", "process-db"],
        )

    def test_missing_env_uses_defaults(self):
        self.assertEqual(self.load_settings(), [None, None, "docauditor"])
