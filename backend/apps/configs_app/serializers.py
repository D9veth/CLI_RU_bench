from rest_framework import serializers

from apps.configs_app.models import DefenseProfile, ModelEndpoint


class DefenseProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DefenseProfile
        fields = (
            "id",
            "name",
            "slug",
            "level",
            "description",
            "yaml_path",
            "parameters_json",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class ModelEndpointSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = ModelEndpoint
        fields = (
            "id",
            "name",
            "display_name",
            "slug",
            "provider",
            "model_name",
            "base_url",
            "default_temperature",
            "default_max_tokens",
            "context_window",
            "is_active",
            "created_at",
            "updated_at",
            "last_check_at",
            "last_check_status",
        )
        read_only_fields = ("id", "display_name", "created_at", "updated_at")

    def get_display_name(self, obj):
        endpoint_name = obj.name or ""
        model_name = obj.model_name or ""
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
