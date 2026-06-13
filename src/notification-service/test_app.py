from fastapi.testclient import TestClient
import pytest
from app import app

client = TestClient(app)

# Tự động mock Kafka Consumer để tránh loop vô hạn hoặc lỗi kết nối cluster khi khởi động app
@pytest.fixture(autouse=True)
def mock_kafka_consumer(mocker):
    # Giả lập class AIOKafkaConsumer
    mock_consumer_class = mocker.patch("app.AIOKafkaConsumer", autospec=True)
    mock_instance = mock_consumer_class.return_value
    
    # Giả lập hàm start, stop
    mock_instance.start = mocker.AsyncMock()
    mock_instance.stop = mocker.AsyncMock()
    
    # Giả lập hành vi lặp (async for) trả về rỗng để tránh block ứng dụng khi test API
    mock_instance.__aiter__.return_value = []
    return mock_instance

def test_health_check():
    response = client.get("/healthz") [cite: 24]
    assert response.status_code == 200 [cite: 24]

def test_send_notification():
    response = client.post("/notify", json={ [cite: 24]
        "email": "customer@gmail.com", [cite: 24]
        "message": "Đơn hàng đã giao" [cite: 24]
    }) [cite: 24]
    assert response.status_code == 200 [cite: 24]
    assert response.json()["status"] == "Sent" [cite: 24]