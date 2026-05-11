from pathlib import Path

from django.core.management.base import BaseCommand

from apps.configs_app.models import DefenseProfile, ModelEndpoint
from apps.datasets.models import Dataset


class Command(BaseCommand):
    help = "Seed idempotent demo data for local backend development."

    def handle(self, *args, **options):
        defense_profiles = [
            ("D0", "Baseline", "configs/defenses/D0.yaml"),
            ("D1", "System prompt", "configs/defenses/D1.yaml"),
            ("D2", "Prefilter wrapping", "configs/defenses/D2.yaml"),
            ("D3", "Postfilter", "configs/defenses/D3.yaml"),
        ]
        for level, name, yaml_path in defense_profiles:
            DefenseProfile.objects.get_or_create(
                slug=level.lower(),
                defaults={
                    "name": name,
                    "level": level,
                    "description": f"Demo defense profile {level}.",
                    "yaml_path": yaml_path,
                },
            )

        repo_root = Path(__file__).resolve().parents[5]
        dataset_candidates = [
            repo_root / "data" / "pilot_20.jsonl",
            repo_root / "data" / "pilot_128.jsonl",
            repo_root / "data" / "sample_ru.yaml",
        ]
        dataset_path = next((path for path in dataset_candidates if path.exists()), None)
        if dataset_path:
            Dataset.objects.get_or_create(
                slug="demo-pilot",
                defaults={
                    "name": "Demo pilot dataset",
                    "description": "Local demo dataset detected in the repository.",
                    "file_path": str(dataset_path.relative_to(repo_root)),
                    "dataset_type": Dataset.DatasetType.PILOT,
                },
            )

        ModelEndpoint.objects.get_or_create(
            slug="local-lm-studio",
            defaults={
                "name": "Local LM Studio",
                "provider": ModelEndpoint.Provider.LMSTUDIO,
                "base_url": "http://localhost:1234/v1",
                "model_name": "local-model",
            },
        )

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
