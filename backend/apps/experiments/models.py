import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


def generate_run_id():
    timestamp = timezone.localtime(timezone.now()).strftime("%Y%m%d_%H%M%S")
    return f"run_{timestamp}_{uuid.uuid4().hex[:8]}"


class BenchmarkRun(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    run_id = models.CharField(max_length=64, unique=True, blank=True)
    title = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="benchmark_runs",
    )
    model_endpoint = models.ForeignKey(
        "configs_app.ModelEndpoint",
        on_delete=models.PROTECT,
        related_name="benchmark_runs",
    )
    dataset = models.ForeignKey(
        "datasets.Dataset",
        on_delete=models.PROTECT,
        related_name="benchmark_runs",
    )
    defense_profile = models.ForeignKey(
        "configs_app.DefenseProfile",
        on_delete=models.PROTECT,
        related_name="benchmark_runs",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    output_dir = models.CharField(max_length=1024, blank=True)
    error_message = models.TextField(blank=True)
    config_snapshot_json = models.JSONField(default=dict, blank=True)
    temperature_override = models.FloatField(null=True, blank=True)
    max_tokens_override = models.PositiveIntegerField(null=True, blank=True)
    extra_params_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def save(self, *args, **kwargs):
        if not self.run_id:
            self.run_id = generate_run_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.run_id}: {self.title}"


class RunMetrics(models.Model):
    run = models.OneToOneField(
        BenchmarkRun,
        on_delete=models.CASCADE,
        related_name="metrics",
    )
    # proxy_asr is the current evaluator's heuristic attack success proxy.
    proxy_asr = models.FloatField(null=True, blank=True)
    one_minus_asr = models.FloatField(null=True, blank=True)
    tpr = models.FloatField(null=True, blank=True)
    fpr = models.FloatField(null=True, blank=True)
    u_mean = models.FloatField(null=True, blank=True)
    rummlu_accuracy = models.FloatField(null=True, blank=True)
    sberquad_f1 = models.FloatField(null=True, blank=True)
    sberquad_em = models.FloatField(null=True, blank=True)
    p50_latency = models.FloatField(null=True, blank=True)
    p95_latency = models.FloatField(null=True, blank=True)
    parse_error_rate = models.FloatField(null=True, blank=True)
    total_cases = models.PositiveIntegerField(default=0)
    ok_cases = models.PositiveIntegerField(default=0)
    error_cases = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "run metrics"

    def __str__(self):
        return f"Metrics for {self.run.run_id}"
