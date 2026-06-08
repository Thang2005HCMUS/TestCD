from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health_check():
    response = client.get("/healthz")
    assert response.status_code == 200

def test_get_all_products():
    response = client.get("/products")
    assert response.status_code == 200
    assert len(response.json()) == 3

def test_get_product_detail_success():
    response = client.get("/products/1")
    assert response.status_code == 200
    assert response.json()["name"] == "Laptop Gaming"

def test_get_product_detail_not_found():
    response = client.get("/products/999")
    assert response.status_code == 404
    #