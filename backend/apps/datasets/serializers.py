from rest_framework import serializers

from apps.datasets.models import Dataset


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "file_path",
            "dataset_type",
            "total_cases",
            "attack_cases",
            "benign_cases",
            "utility_cases",
            "rummlu_cases",
            "sberquad_cases",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
