import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_token_login_and_me_returns_user_role(django_user_model):
    user = django_user_model.objects.create_user(
        username="viewer",
        email="viewer@example.com",
        password="test-password",
        role=django_user_model.Role.VIEWER,
    )
    client = APIClient()

    token_response = client.post(
        "/api/auth/token/",
        {"username": user.username, "password": "test-password"},
        format="json",
    )

    assert token_response.status_code == 200
    assert "access" in token_response.data

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}")
    me_response = client.get("/api/auth/me/")

    assert me_response.status_code == 200
    assert me_response.data["username"] == user.username
    assert me_response.data["role"] == django_user_model.Role.VIEWER
