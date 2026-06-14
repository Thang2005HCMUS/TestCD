import pytest
import httpx
import time

@pytest.fixture
def k8s_namespace(request):
    return request.config.getoption("--ns")

@pytest.fixture
def base_url(k8s_namespace):
    return f"http://product-service.{k8s_namespace}.svc.cluster.local:8000"

def test_product_service_ready(base_url):
    """Đợi Pod Product Service lên trạng thái Ready"""
    for _ in range(10):
        try:
            response = httpx.get(f"{base_url}/healthz")
            if response.status_code == 200:
                return
        except httpx.RequestError:
            time.sleep(2)
    pytest.fail("Product Service không phản hồi")

def test_get_product_catalog_and_detail(base_url):
    """Kiểm tra lấy danh sách sản phẩm và chi tiết sản phẩm 1"""
    # Test API lấy tất cả sản phẩm
    list_resp = httpx.get(f"{base_url}/products")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 3

    # Test API lấy chi tiết Laptop Gaming (ID = 1)
    detail_resp = httpx.get(f"{base_url}/products/1")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["name"] == "Laptop Gaming"
    assert detail_resp.json()["price"] == 1500