from django.contrib import admin

from apps.experiments.models import BenchmarkRun, RunMetrics


@admin.register(BenchmarkRun)
class BenchmarkRunAdmin(admin.ModelAdmin):
    list_display = (
        "run_id",
        "title",
        "status",
        "model_endpoint",
        "dataset",
        "defense_profile",
        "created_by",
        "created_at",
    )
    list_filter = ("status", "model_endpoint", "dataset", "defense_profile")
    search_fields = ("run_id", "title", "output_dir")
    readonly_fields = ("created_at", "updated_at")


@admin.register(RunMetrics)
class RunMetricsAdmin(admin.ModelAdmin):
    list_display = (
        "run",
        "proxy_asr",
        "one_minus_asr",
        "tpr",
        "fpr",
        "u_mean",
        "total_cases",
        "updated_at",
    )
    search_fields = ("run__run_id", "run__title")
    readonly_fields = ("created_at", "updated_at")
