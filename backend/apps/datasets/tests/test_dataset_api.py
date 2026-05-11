import pytest
from rest_framework.test import APIClient

from apps.datasets.models import Dataset


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_viewer_can_read_datasets(django_user_model):
    user = django_user_model.objects.create_user(
        username="viewer",
        password="test-password",
        role=django_user_model.Role.VIEWER,
    )
    Dataset.objects.create(
        name="Pilot 20",
        slug="pilot-20",
        file_path="data/pilot_20.jsonl",
        dataset_type=Dataset.DatasetType.PILOT,
    )

    response = client_for(user).get("/api/datasets/")

    assert response.status_code == 200
    assert response.data[0]["slug"] == "pilot-20"


@pytest.mark.django_db
def test_researcher_can_create_dataset(django_user_model):
    user = django_user_model.objects.create_user(
        username="researcher",
        password="test-password",
        role=django_user_model.Role.RESEARCHER,
    )
    payload = {
        "name": "Generated dataset",
        "slug": "generated-dataset",
        "file_path": "data/generated.jsonl",
        "dataset_type": Dataset.DatasetType.GENERATED,
    }

    response = client_for(user).post("/api/datasets/", payload, format="json")

    assert response.status_code == 201
    assert Dataset.objects.filter(slug="generated-dataset").exists()


@pytest.mark.django_db
def test_viewer_cannot_create_dataset(django_user_model):
    user = django_user_model.objects.create_user(
        username="viewer",
        password="test-password",
        role=django_user_model.Role.VIEWER,
    )
    payload = {
        "name": "Blocked dataset",
        "slug": "blocked-dataset",
        "file_path": "data/blocked.jsonl",
        "dataset_type": Dataset.DatasetType.SAMPLE,
    }

    response = client_for(user).post("/api/datasets/", payload, format="json")

    assert response.status_code == 403
