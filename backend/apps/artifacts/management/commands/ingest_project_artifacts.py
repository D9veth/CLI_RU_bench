import json
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.artifacts.models import ProjectArtifact
from apps.artifacts.services.project_artifact_scanner import (
    get_repo_root,
    import_all_project_artifacts,
)


class Command(BaseCommand):
    help = "Import useful repository artifacts into the backend database."

    def add_arguments(self, parser):
        parser.add_argument("--root", type=str, default=None, help="Repository root path.")
        parser.add_argument("--dry-run", action="store_true", help="Only show what would be imported.")
        parser.add_argument("--verbose", action="store_true", help="Print import summary as formatted JSON.")
        parser.add_argument(
            "--type",
            type=str,
            default=None,
            choices=[choice[0] for choice in ProjectArtifact.ArtifactType.choices],
            help="Optional ProjectArtifact artifact_type filter.",
        )

    def handle(self, *args, **options):
        repo_root = Path(options["root"]).resolve() if options["root"] else get_repo_root()
        summary = import_all_project_artifacts(
            repo_root=repo_root,
            dry_run=options["dry_run"],
            artifact_type=options["type"],
        )
        indent = 2 if options["verbose"] else None
        self.stdout.write(json.dumps(summary, ensure_ascii=False, indent=indent))
