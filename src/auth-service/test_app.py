from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health_check():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "auth-service"}

def test_login_success():
    response = client.post("/login", json={"username": "admin", "password": "password"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_fail():
    response = client.post("/login", json={"username": "wrong", "password": "password"})
    assert response.status_code == 401