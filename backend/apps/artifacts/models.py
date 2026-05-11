from django.db import models


class RunArtifact(models.Model):
    class ArtifactType(models.TextChoices):
        RUN_CONFIG = "run_config", "Run config"
        PREFLIGHT = "preflight", "Preflight"
        CASES = "cases", "Cases"
        SUMMARY = "summary", "Summary"
        REPORT = "report", "Report"
        CSV = "csv", "CSV"
        FIGURE = "figure", "Figure"
        LOG = "log", "Log"
        OTHER = "other", "Other"

    run = models.ForeignKey(
        "experiments.BenchmarkRun",
        on_delete=models.CASCADE,
        related_name="artifacts",
    )
    artifact_type = models.CharField(
        max_length=40,
        choices=ArtifactType.choices,
        default=ArtifactType.OTHER,
    )
    file_path = models.CharField(max_length=1024)
    size_bytes = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["run", "artifact_type", "id"]

    def __str__(self):
        return f"{self.artifact_type}: {self.file_path}"


class ProjectArtifact(models.Model):
    class ArtifactType(models.TextChoices):
        DATASET = "dataset", "Dataset"
        CONFIG = "config", "Config"
        RUN_ARTIFACT = "run_artifact", "Run artifact"
        REPORT = "report", "Report"
        TABLE = "table", "Table"
        FIGURE = "figure", "Figure"
        JSON = "json", "JSON"
        JSONL = "jsonl", "JSONL"
        LOG = "log", "Log"
        MARKDOWN = "markdown", "Markdown"
        DOCUMENT = "document", "Document"
        SCRIPT = "script", "Script"
        OTHER = "other", "Other"

    name = models.CharField(max_length=255)
    artifact_type = models.CharField(
        max_length=40,
        choices=ArtifactType.choices,
        default=ArtifactType.OTHER,
    )
    file_path = models.CharField(max_length=1024, unique=True)
    source_dir = models.CharField(max_length=120, blank=True)
    extension = models.CharField(max_length=20, blank=True)
    size_bytes = models.BigIntegerField(default=0)
    line_count = models.PositiveIntegerField(null=True, blank=True)
    sha256 = models.CharField(max_length=64, blank=True)
    related_run = models.ForeignKey(
        "experiments.BenchmarkRun",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_artifacts",
    )
    related_dataset = models.ForeignKey(
        "datasets.Dataset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_artifacts",
    )
    related_defense_profile = models.ForeignKey(
        "configs_app.DefenseProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_artifacts",
    )
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["source_dir", "artifact_type", "file_path"]

    def __str__(self):
        return f"{self.artifact_type}: {self.file_path}"
