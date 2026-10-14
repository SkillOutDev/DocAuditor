from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "analysis_status", "created_at")
    list_filter = ("analysis_status", "created_at")
    search_fields = ("title", "original_filename", "owner__username")
