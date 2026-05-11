from django.db import models


class DefenseProfile(models.Model):
    class Level(models.TextChoices):
        D0 = "D0", "D0"
        D1 = "D1", "D1"
        D2 = "D2", "D2"
        D3 = "D3", "D3"
        CUSTOM = "custom", "Custom"

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    level = models.CharField(max_length=20, choices=Level.choices)
    description = models.TextField(blank=True)
    yaml_path = models.CharField(max_length=1024, blank=True)
    parameters_json = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["level", "name"]

    def __str__(self):
        return f"{self.level}: {self.name}"


class ModelEndpoint(models.Model):
    class Provider(models.TextChoices):
        LMSTUDIO = "lmstudio", "LM Studio"
        OLLAMA = "ollama", "Ollama"
        OPENAI_COMPATIBLE = "openai_compatible", "OpenAI Compatible"
        OTHER = "other", "Other"

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    provider = models.CharField(max_length=40, choices=Provider.choices)
    model_name = models.CharField(max_length=255)
    base_url = models.URLField(max_length=1024)
    default_temperature = models.FloatField(default=0.2)
    default_max_tokens = models.PositiveIntegerField(default=1024)
    context_window = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_check_at = models.DateTimeField(null=True, blank=True)
    last_check_status = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.model_name})"
