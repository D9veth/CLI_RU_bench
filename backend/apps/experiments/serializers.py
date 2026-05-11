from rest_framework import serializers

from apps.experiments.models import BenchmarkRun, RunMetrics


class RunMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RunMetrics
        fields = (
            "id",
            "run",
            "proxy_asr",
            "one_minus_asr",
            "tpr",
            "fpr",
            "u_mean",
            "rummlu_accuracy",
            "sberquad_f1",
            "sberquad_em",
            "p50_latency",
            "p95_latency",
            "parse_error_rate",
            "total_cases",
            "ok_cases",
            "error_cases",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class BenchmarkRunSerializer(serializers.ModelSerializer):
    temperature = serializers.FloatField(required=False, write_only=True, allow_null=True)
    max_tokens = serializers.IntegerField(required=False, write_only=True, allow_null=True, min_value=1)
    extra_params = serializers.JSONField(required=False, write_only=True)
    model_endpoint_name = serializers.SerializerMethodField()
    dataset_name = serializers.CharField(source="dataset.name", read_only=True)
    defense_profile_name = serializers.CharField(source="defense_profile.name", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)
    metrics = RunMetricsSerializer(read_only=True)
    can_start = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()
    logs_available = serializers.SerializerMethodField()
    artifacts_count = serializers.SerializerMethodField()

    class Meta:
        model = BenchmarkRun
        fields = (
            "id",
            "run_id",
            "title",
            "created_by",
            "created_by_username",
            "model_endpoint",
            "model_endpoint_name",
            "dataset",
            "dataset_name",
            "defense_profile",
            "defense_profile_name",
            "status",
            "started_at",
            "finished_at",
            "output_dir",
            "error_message",
            "config_snapshot_json",
            "temperature",
            "max_tokens",
            "extra_params",
            "temperature_override",
            "max_tokens_override",
            "extra_params_json",
            "metrics",
            "can_start",
            "can_cancel",
            "logs_available",
            "artifacts_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_by",
            "created_by_username",
            "model_endpoint_name",
            "dataset_name",
            "defense_profile_name",
            "metrics",
            "can_start",
            "can_cancel",
            "logs_available",
            "artifacts_count",
            "created_at",
            "updated_at",
        )
        extra_kwargs = {
            "run_id": {"required": False, "allow_blank": True},
            "status": {"required": False},
            "config_snapshot_json": {"required": False},
        }

    def create(self, validated_data):
        self._normalize_runtime_fields(validated_data)
        if not validated_data.get("config_snapshot_json"):
            validated_data["config_snapshot_json"] = self._build_config_snapshot(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        self._normalize_runtime_fields(validated_data)
        return super().update(instance, validated_data)

    def get_can_start(self, obj):
        return obj.status == BenchmarkRun.Status.PENDING

    def get_model_endpoint_name(self, obj):
        return _model_display_name(obj.model_endpoint)

    def get_can_cancel(self, obj):
        return obj.status in {BenchmarkRun.Status.PENDING, BenchmarkRun.Status.RUNNING}

    def get_logs_available(self, obj):
        return obj.artifacts.filter(file_path__iendswith=".log").exists()

    def get_artifacts_count(self, obj):
        return obj.artifacts.count()

    def _build_config_snapshot(self, data):
        model_endpoint = data["model_endpoint"]
        dataset = data["dataset"]
        defense_profile = data["defense_profile"]
        return {
            "model_endpoint": {
                "name": model_endpoint.name,
                "model_name": model_endpoint.model_name,
                "base_url": model_endpoint.base_url,
                "provider": model_endpoint.provider,
            },
            "dataset": {
                "name": dataset.name,
                "file_path": dataset.file_path,
                "dataset_type": dataset.dataset_type,
            },
            "defense_profile": {
                "name": defense_profile.name,
                "level": defense_profile.level,
                "yaml_path": defense_profile.yaml_path,
                "parameters_json": defense_profile.parameters_json,
            },
            "runtime": {
                "temperature": data.get("temperature_override"),
                "max_tokens": data.get("max_tokens_override"),
                "extra_params": data.get("extra_params_json", {}),
            },
        }

    def _normalize_runtime_fields(self, data):
        if "temperature" in data:
            data["temperature_override"] = data.pop("temperature")
        if "max_tokens" in data:
            data["max_tokens_override"] = data.pop("max_tokens")
        if "extra_params" in data:
            data["extra_params_json"] = data.pop("extra_params") or {}


def _model_display_name(endpoint) -> str:
    endpoint_name = endpoint.name or ""
    model_name = endpoint.model_name or ""
    normalized_name = endpoint_name.lower().replace("_", " ").replace("-", " ").strip()
    generic_local_names = {
        "local llm",
        "local lm studio",
        "local lmstudio",
        "unknown model endpoint",
    }
    if model_name and (not endpoint_name or normalized_name in generic_local_names):
        return model_name
    if endpoint_name and model_name and model_name.lower() not in endpoint_name.lower():
        return f"{endpoint_name} · {model_name}"
    return endpoint_name or model_name
