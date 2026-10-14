from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx"}
MAX_DOCUMENT_SIZE = 15 * 1024 * 1024


def validate_document_file(uploaded_file):
    extension = Path(uploaded_file.name).suffix.lower()
    if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise ValidationError("Leidžiami tik PDF, DOC ir DOCX failai.")
    if uploaded_file.size > MAX_DOCUMENT_SIZE:
        raise ValidationError("Dokumento dydis negali viršyti 15 MB.")


class Document(models.Model):
    class AnalysisStatus(models.TextChoices):
        PENDING = "pending", "Laukiama"
        ANALYZING = "analyzing", "Analizuojama"
        COMPLETED = "completed", "Baigta"
        FAILED = "failed", "Nepavyko"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="documents/%Y/%m/", validators=[validate_document_file])
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveBigIntegerField()
    content_type = models.CharField(max_length=100, blank=True)
    analysis_status = models.CharField(
        max_length=20,
        choices=AnalysisStatus.choices,
        default=AnalysisStatus.PENDING,
    )
    simplified_explanation = models.TextField(blank=True)
    key_conditions = models.JSONField(default=list, blank=True)
    analysis_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.file and not self.original_filename:
            self.original_filename = Path(self.file.name).name
        if self.file and not self.file_size:
            self.file_size = self.file.size
        if self.file and not self.title:
            self.title = Path(self.file.name).stem
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
