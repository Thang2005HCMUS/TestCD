# Mock các cuộc gọi HTTP ra bên ngoài
from fastapi.testclient import TestClient
import pytest
from app import app

client = TestClient(app)

# Tự động mock Kafka Producer cho toàn bộ các test case trong file này
@pytest.fixture(autouse=True)
def mock_kafka_producer(mocker):
    # Giả lập class AIOKafkaProducer
    mock_producer_class = mocker.patch("app.AIOKafkaProducer", autospec=True)
    # Giả lập instance được tạo ra sau khi gọi AIOKafkaProducer()
    mock_instance = mock_producer_class.return_value
    # Giả lập các hàm async start, stop và send_and_wait thành các hàm không làm gì (AsyncMock)
    mock_instance.start = mocker.AsyncMock()
    mock_instance.stop = mocker.AsyncMock()
    mock_instance.send_and_wait = mocker.AsyncMock()
    return mock_instance

def test_health_check():
    response = client.get("/healthz")
    assert response.status_code == 200

# Mock các cuộc gọi HTTP ra bên ngoài và kiểm tra logic gửi Kafka
@pytest.mark.asyncio
async def test_create_order_success(mocker):
    # Giả lập Product Service trả về thông tin Laptop 
    mock_product_resp = mocker.Mock() 
    mock_product_resp.status_code = 200 
    mock_product_resp.json.return_value = {"name": "Laptop Gaming", "price": 1500} 
    
    # Khởi tạo mock cho AsyncClient của httpx 
    mock_client = mocker.patch("httpx.AsyncClient", autospec=True) 
    mock_instance = mock_client.return_value.__aenter__.return_value 
    mock_instance.get.return_value = mock_product_resp 

    # Chạy test API tạo đơn hàng
    response = client.post("/orders", json={ 
        "product_id": 1, 
        "quantity": 2, 
        "user_email": "test@gmail.com" 
    }) 
    
    assert response.status_code == 200 
    assert response.json()["order_status"] == "Success" 
    assert response.json()["total_price"] == 3000 