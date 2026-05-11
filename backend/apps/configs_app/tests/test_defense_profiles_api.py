import pytest
from rest_framework.test import APIClient

from apps.configs_app.models import DefenseProfile


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_viewer_can_read_defense_profiles(django_user_model):
    user = django_user_model.objects.create_user(
        username="viewer",
        password="test-password",
        role=django_user_model.Role.VIEWER,
    )
    DefenseProfile.objects.create(
        name="Baseline",
        slug="d0",
        level=DefenseProfile.Level.D0,
    )

    response = client_for(user).get("/api/defense-profiles/")

    assert response.status_code == 200
    assert response.data[0]["level"] == DefenseProfile.Level.D0


@pytest.mark.django_db
def test_researcher_can_create_defense_profile(django_user_model):
    user = django_user_model.objects.create_user(
        username="researcher",
        password="test-password",
        role=django_user_model.Role.RESEARCHER,
    )
    payload = {
        "name": "Custom defense",
        "slug": "custom-defense",
        "level": DefenseProfile.Level.CUSTOM,
        "parameters_json": {"mode": "demo"},
    }

    response = client_for(user).post("/api/defense-profiles/", payload, format="json")

    assert response.status_code == 201
    assert DefenseProfile.objects.filter(slug="custom-defense").exists()
