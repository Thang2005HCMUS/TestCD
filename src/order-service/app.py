import os
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Order Service")

# K8s sẽ phân giải DNS nội bộ dạng http://<service-name>:<port>
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8000")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8000")

class OrderRequest(BaseModel):
    product_id: int
    quantity: int
    user_email: str

@app.get("/healthz")
def health_check():
    return {"status": "healthy", "service": "order-service"}

@app.post("/orders")#
async def create_order(order: OrderRequest):
    # 1. Gọi sang Product Service lấy thông tin sản phẩm
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{PRODUCT_SERVICE_URL}/products/{order.product_id}")
            if response.status_code == 404:
                raise HTTPException(status_code=400, detail="Sản phẩm không tồn tại")
            product_data = response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Không thể kết nối tới Product Service")

    # 2. Tính toán tổng tiền
    total_price = product_data["price"] * order.quantity
    
    # 3. Gửi thông báo ngầm sang Notification Service (Fire and Forget)
    async with httpx.AsyncClient() as client:
        try:
            await client.post(f"{NOTIFICATION_SERVICE_URL}/notify", json={
                "email": order.user_email,
                "message": f"Bạn đã đặt hàng thành công đơn hàng {product_data['name']}. Tổng tiền: ${total_price}"
            })
        except httpx.RequestError:
            print("Cảnh báo: Không thể gửi thông báo, nhưng đơn hàng vẫn được xử lý.")

    return {
        "order_status": "Success",
        "product_name": product_data["name"],
        "total_price": total_price
    }