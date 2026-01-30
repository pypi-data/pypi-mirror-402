import pytest
from django.test import Client


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
def test_health_endpoint_should_return_200(client):
    response = client.get("/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.django_db
def test_ready_endpoint_should_return_200_when_all_services_healthy(client):
    response = client.get("/ready/")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["checks"]["database"]["status"] == "ok"
    assert data["checks"]["cache"]["status"] == "ok"


@pytest.mark.django_db
def test_ready_endpoint_should_include_check_details(client):
    response = client.get("/ready/")

    data = response.json()
    assert "checks" in data
    assert "database" in data["checks"]
    assert "cache" in data["checks"]
