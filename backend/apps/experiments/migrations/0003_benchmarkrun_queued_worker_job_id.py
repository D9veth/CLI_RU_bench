from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0002_benchmarkrun_extra_params_json_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="benchmarkrun",
            name="worker_job_id",
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AlterField(
            model_name="benchmarkrun",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("queued", "Queued"),
                    ("running", "Running"),
                    ("completed", "Completed"),
                    ("failed", "Failed"),
                    ("cancelled", "Cancelled"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
    ]
