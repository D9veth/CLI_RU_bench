from django.db import models


class Dataset(models.Model):
    class DatasetType(models.TextChoices):
        FULL = "full", "Full"
        PILOT = "pilot", "Pilot"
        SAMPLE = "sample", "Sample"
        GENERATED = "generated", "Generated"
        UNKNOWN = "unknown", "Unknown"

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    file_path = models.CharField(max_length=1024)
    dataset_type = models.CharField(
        max_length=20,
        choices=DatasetType.choices,
        default=DatasetType.UNKNOWN,
    )
    total_cases = models.PositiveIntegerField(default=0)
    attack_cases = models.PositiveIntegerField(default=0)
    benign_cases = models.PositiveIntegerField(default=0)
    utility_cases = models.PositiveIntegerField(default=0)
    rummlu_cases = models.PositiveIntegerField(default=0)
    sberquad_cases = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
