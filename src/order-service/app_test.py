from fastapi.testclient import TestClient
import pytest
from app import app

client = TestClient(app)

def test_health_check():
    response = client.get("/healthz")
    assert response.status_code == 200

# Mock các cuộc gọi HTTP ra bên ngoài
@pytest.mark.asyncio
async def test_create_order_success(mocker):
    # Giả lập Product Service trả về thông tin Laptop
    mock_product_resp = mocker.Mock()
    mock_product_resp.status_code = 200
    mock_product_resp.json.return_value = {"name": "Laptop Gaming", "price": 1500}
    
    # Giả lập Notification Service trả về thành công
    mock_notify_resp = mocker.Mock()
    mock_notify_resp.status_code = 200

    # Khởi tạo mock cho AsyncClient
    mock_client = mocker.patch("httpx.AsyncClient", autospec=True)
    mock_instance = mock_client.return_value.__aenter__.return_value
    mock_instance.get.return_value = mock_product_resp
    mock_instance.post.return_value = mock_notify_resp

    # Chạy test
    response = client.post("/orders", json={
        "product_id": 1,
        "quantity": 2,
        "user_email": "test@gmail.com"
    })
    
    assert response.status_code == 200
    assert response.json()["order_status"] == "Success"
    assert response.json()["total_price"] == 3000