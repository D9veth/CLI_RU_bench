from pathlib import Path

from django.core.management.base import BaseCommand

from apps.experiments.services.artifact_ingestion import (
    find_run_dirs,
    get_repo_root,
    import_all_runs,
    parse_run_dir,
)


class Command(BaseCommand):
    help = "Import existing CLI run artifacts into the backend database."

    def add_arguments(self, parser):
        parser.add_argument("--root", type=str, default=None, help="Repository root path.")
        parser.add_argument("--dry-run", action="store_true", help="Only show what would be imported.")
        parser.add_argument("--verbose", action="store_true", help="Print each detected run directory.")

    def handle(self, *args, **options):
        repo_root = Path(options["root"]).resolve() if options["root"] else get_repo_root()
        dry_run = options["dry_run"]
        verbose = options["verbose"]

        if dry_run:
            run_dirs = find_run_dirs(repo_root)
            for run_dir in run_dirs:
                parsed = parse_run_dir(run_dir)
                if verbose:
                    self.stdout.write(
                        f"would import {parsed['run_id']} from {parsed['output_dir']}"
                    )
            summary = {
                "found": len(run_dirs),
                "imported": 0,
                "updated": 0,
                "skipped": 0,
                "errors": [],
            }
        else:
            summary = import_all_runs(repo_root)

        self.stdout.write(
            "found={found} imported={imported} updated={updated} skipped={skipped}".format(
                **summary
            )
        )
        if summary["errors"]:
            for error in summary["errors"]:
                self.stderr.write(f"{error['path']}: {error['error']}")
