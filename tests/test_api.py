import pytest
import requests
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

@pytest.fixture
def api_client():
    """Client API basé sur requests (pas besoin de TestClient)"""
    return requests.Session()

def test_health_check(api_client):
    """Test du endpoint de santé"""
    response = api_client.get(f"{BASE_URL}/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_system_status(api_client):
    """Test du endpoint système"""
    response = api_client.get(f"{BASE_URL}/system/status")
    assert response.status_code == 200
    data: Dict[str, Any] = response.json()
    assert "status" in data
    assert isinstance(data.get("workers"), list)

def test_task_creation(api_client):
    """Test de création de tâche"""
    test_data = {
        "urls": ["https://www.example.com"],  # URL neutre pour les tests
        "mode": "auto"
    }
    response = api_client.post(
        f"{BASE_URL}/tasks",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code in [200, 201]
    assert "task_id" in response.json()