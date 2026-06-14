import pytest
import httpx
import time

@pytest.fixture
def k8s_namespace(request):
    return request.config.getoption("--ns")

@pytest.fixture
def base_url(k8s_namespace):
    return f"http://auth-service.{k8s_namespace}.svc.cluster.local:8000"

def test_auth_service_ready(base_url):
    """Đợi Pod Auth Service lên trạng thái Ready"""
    for _ in range(10):
        try:
            response = httpx.get(f"{base_url}/healthz")
            if response.status_code == 200:
                return
        except httpx.RequestError:
            time.sleep(2)
    pytest.fail("Auth Service không phản hồi trong K8s Namespace tạm")

def test_auth_full_login_and_verify_flow(base_url):
    """Test login thật -> Lấy token -> Gọi API verify token thật"""
    # 1. Gọi login
    login_payload = {"username": "admin", "password": "password"}
    login_resp = httpx.post(f"{base_url}/login", json=login_payload)
    assert login_resp.status_code == 200
    
    token = login_resp.json()["access_token"]
    assert token == "mock-token-for-admin"

    # 2. Gọi verify bằng token vừa nhận
    verify_resp = httpx.get(f"{base_url}/verify/{token}")
    assert verify_resp.status_code == 200
    assert verify_resp.json()["valid"] is True
    assert verify_resp.json()["user"] == "admin"