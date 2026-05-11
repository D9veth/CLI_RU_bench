from django.contrib import admin

from apps.datasets.models import Dataset


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "dataset_type",
        "total_cases",
        "is_active",
        "updated_at",
    )
    list_filter = ("dataset_type", "is_active")
    search_fields = ("name", "slug", "file_path")
    readonly_fields = ("created_at", "updated_at")
