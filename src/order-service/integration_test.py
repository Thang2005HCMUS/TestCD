import pytest
import httpx
import time

@pytest.fixture
def k8s_namespace(request):
    return request.config.getoption("--ns")

@pytest.fixture
def base_url(k8s_namespace):
    return f"http://order-service.{k8s_namespace}.svc.cluster.local:8000"

@pytest.fixture
def product_service_url(k8s_namespace):
    return f"http://product-service.{k8s_namespace}.svc.cluster.local:8000"

def test_order_and_dependencies_ready(base_url, product_service_url):
    """Đợi cả Order Service lẫn Product Service sẵn sàng"""
    for _ in range(15):
        try:
            res1 = httpx.get(f"{base_url}/healthz")
            res2 = httpx.get(f"{product_service_url}/healthz")
            if res1.status_code == 200 and res2.status_code == 200:
                return
        except httpx.RequestError:
            time.sleep(3)
    pytest.fail("Hạ tầng dịch vụ Order/Product chưa sẵn sàng kết nối")

def test_create_order_integration_flow(base_url):
    """Bắn đơn hàng thật, kiểm tra tính toán tổng tiền kết nối liên thông qua Product Service"""
    order_payload = {
        "product_id": 2,      # Bàn phím cơ
        "quantity": 5,        # Số lượng 5 chiếc (Giá gốc $100)
        "user_email": "k8s-tester@gmail.com"
    }
    
    response = httpx.post(f"{base_url}/orders", json=order_payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["order_status"] == "Success"
    assert data["product_name"] == "Bàn phím cơ"
    assert data["total_price"] == 500  # 100 * 5 = 500