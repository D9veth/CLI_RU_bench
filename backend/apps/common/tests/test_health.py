import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_is_available_without_authentication():
    response = APIClient().get("/api/health/")

    assert response.status_code == 200
    assert response.data["status"] == "ok"
    assert response.data["service"] == "llm-bench-backend"
