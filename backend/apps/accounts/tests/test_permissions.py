import pytest
from rest_framework.test import APIClient


def authenticated_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_viewer_cannot_list_users(django_user_model):
    user = django_user_model.objects.create_user(
        username="viewer",
        password="test-password",
        role=django_user_model.Role.VIEWER,
    )

    response = authenticated_client(user).get("/api/auth/users/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_researcher_cannot_list_users(django_user_model):
    user = django_user_model.objects.create_user(
        username="researcher",
        password="test-password",
        role=django_user_model.Role.RESEARCHER,
    )

    response = authenticated_client(user).get("/api/auth/users/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_role_can_list_users(django_user_model):
    user = django_user_model.objects.create_user(
        username="admin",
        password="test-password",
        role=django_user_model.Role.ADMIN,
    )

    response = authenticated_client(user).get("/api/auth/users/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_superuser_is_treated_as_admin(django_user_model):
    user = django_user_model.objects.create_superuser(
        username="superuser",
        password="test-password",
    )

    response = authenticated_client(user).get("/api/auth/users/")

    assert user.role == django_user_model.Role.ADMIN
    assert response.status_code == 200
