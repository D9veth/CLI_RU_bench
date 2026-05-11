from rest_framework import serializers

from apps.artifacts.models import ProjectArtifact, RunArtifact


class RunArtifactSerializer(serializers.ModelSerializer):
    run_id = serializers.CharField(source="run.run_id", read_only=True)
    run_title = serializers.CharField(source="run.title", read_only=True)

    class Meta:
        model = RunArtifact
        fields = (
            "id",
            "run",
            "run_id",
            "run_title",
            "artifact_type",
            "file_path",
            "size_bytes",
            "created_at",
        )
        read_only_fields = ("id", "run_id", "run_title", "created_at")


class ProjectArtifactSerializer(serializers.ModelSerializer):
    related_run_id = serializers.CharField(source="related_run.run_id", read_only=True)
    related_run_title = serializers.CharField(source="related_run.title", read_only=True)
    related_dataset_name = serializers.CharField(source="related_dataset.name", read_only=True)
    related_defense_profile_name = serializers.CharField(source="related_defense_profile.name", read_only=True)

    class Meta:
        model = ProjectArtifact
        fields = (
            "id",
            "name",
            "artifact_type",
            "file_path",
            "source_dir",
            "extension",
            "size_bytes",
            "line_count",
            "sha256",
            "related_run",
            "related_run_id",
            "related_run_title",
            "related_dataset",
            "related_dataset_name",
            "related_defense_profile",
            "related_defense_profile_name",
            "metadata_json",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "related_run_id",
            "related_run_title",
            "related_dataset_name",
            "related_defense_profile_name",
            "created_at",
            "updated_at",
        )
