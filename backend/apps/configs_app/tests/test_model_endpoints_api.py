import pytest
from rest_framework.test import APIClient

from apps.configs_app.models import ModelEndpoint


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_researcher_can_create_model_endpoint(django_user_model):
    user = django_user_model.objects.create_user(
        username="researcher",
        password="test-password",
        role=django_user_model.Role.RESEARCHER,
    )
    payload = {
        "name": "Local LM Studio",
        "slug": "local-lm-studio",
        "provider": ModelEndpoint.Provider.LMSTUDIO,
        "model_name": "local-model",
        "base_url": "http://localhost:1234/v1",
    }

    response = client_for(user).post("/api/model-endpoints/", payload, format="json")

    assert response.status_code == 201
    assert ModelEndpoint.objects.filter(slug="local-lm-studio").exists()


@pytest.mark.django_db
def test_viewer_cannot_create_model_endpoint(django_user_model):
    user = django_user_model.objects.create_user(
        username="viewer",
        password="test-password",
        role=django_user_model.Role.VIEWER,
    )
    payload = {
        "name": "Blocked endpoint",
        "slug": "blocked-endpoint",
        "provider": ModelEndpoint.Provider.OTHER,
        "model_name": "blocked-model",
        "base_url": "http://localhost:1234/v1",
    }

    response = client_for(user).post("/api/model-endpoints/", payload, format="json")

    assert response.status_code == 403
