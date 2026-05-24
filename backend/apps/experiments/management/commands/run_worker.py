import time

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.experiments.models import BenchmarkRun
from apps.experiments.services.run_executor import execute_run


class Command(BaseCommand):
    help = "Run a simple DB-backed benchmark worker for queued runs."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Process one queued run and exit.")
        parser.add_argument("--sleep", type=float, default=2.0, help="Polling sleep in seconds.")

    def handle(self, *args, **options):
        once = options["once"]
        sleep = options["sleep"]
        while True:
            run_id = self._claim_next_run()
            if run_id is None:
                if once:
                    return
                time.sleep(sleep)
                continue
            execute_run(run_id)
            if once:
                return

    @transaction.atomic
    def _claim_next_run(self):
        run = (
            BenchmarkRun.objects.select_for_update(skip_locked=True)
            .filter(status=BenchmarkRun.Status.QUEUED)
            .order_by("created_at", "id")
            .first()
        )
        return run.id if run else None
