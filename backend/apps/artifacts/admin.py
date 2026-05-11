from django.contrib import admin

from apps.artifacts.models import ProjectArtifact, RunArtifact


@admin.register(RunArtifact)
class RunArtifactAdmin(admin.ModelAdmin):
    list_display = ("run", "artifact_type", "file_path", "size_bytes", "created_at")
    list_filter = ("artifact_type",)
    search_fields = ("run__run_id", "run__title", "file_path")
    readonly_fields = ("created_at",)


@admin.register(ProjectArtifact)
class ProjectArtifactAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "artifact_type",
        "source_dir",
        "extension",
        "size_bytes",
        "related_run",
        "updated_at",
    )
    list_filter = ("artifact_type", "source_dir", "extension")
    search_fields = (
        "name",
        "file_path",
        "related_run__run_id",
        "related_dataset__name",
        "related_defense_profile__name",
    )
    readonly_fields = ("created_at", "updated_at")
