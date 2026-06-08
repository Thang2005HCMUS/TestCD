from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health_check():
    response = client.get("/healthz")
    assert response.status_code == 200

def test_send_notification():
    response = client.post("/notify", json={
        "email": "customer@gmail.com",
        "message": "Đơn hàng đã giao"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "Sent"