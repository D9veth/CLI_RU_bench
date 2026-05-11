from django.contrib import admin

from apps.configs_app.models import DefenseProfile, ModelEndpoint


@admin.register(DefenseProfile)
class DefenseProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "level", "is_active", "updated_at")
    list_filter = ("level", "is_active")
    search_fields = ("name", "slug", "yaml_path")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ModelEndpoint)
class ModelEndpointAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "provider",
        "model_name",
        "is_active",
        "last_check_status",
        "updated_at",
    )
    list_filter = ("provider", "is_active")
    search_fields = ("name", "slug", "model_name", "base_url")
    readonly_fields = ("created_at", "updated_at")
