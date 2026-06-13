import os
import json
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from aiokafka import AIOKafkaProducer

app = FastAPI(title="Order Service")

PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8000")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-service:9092")
TOPIC_NAME = "order-notifications"

class OrderRequest(BaseModel):
    product_id: int
    quantity: int
    user_email: str

# Khởi tạo Kafka Producer toàn cục
producer = None

@app.on_event("startup")
async def startup_event():
    global producer
    try:
        producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        await producer.start()
        print(f" Kafka Producer started successfully matching cluster: {KAFKA_BOOTSTRAP_SERVERS}")
    except Exception as e:
        print(f"❌ Failed to start Kafka Producer: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    global producer
    if producer:
        await producer.stop()

@app.get("/healthz")
def health_check():
    return {"status": "healthy", "service": "order-service"}

@app.post("/orders")
async def create_order(order: OrderRequest):
    # 1. Gọi sang Product Service lấy thông tin sản phẩm [cite: 10]
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{PRODUCT_SERVICE_URL}/products/{order.product_id}")
            if response.status_code == 404:
                raise HTTPException(status_code=400, detail="Sản phẩm không tồn tại")
            product_data = response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Không thể kết nối tới Product Service") 

    # 2. Tính toán tổng tiền [cite: 12]
    total_price = product_data["price"] * order.quantity
    
    # 3. Gửi Event vào Kafka thay vì gọi HTTP direct sang Notification Service [cite: 12]
    event_message = {
        "email": order.user_email,
        "message": f"Bạn đã đặt hàng thành công đơn hàng {product_data['name']}. Tổng tiền: ${total_price}" 
    }
    
    if producer:
        try:
            payload = json.dumps(event_message).encode('utf-8')
            await producer.send_and_wait(TOPIC_NAME, payload)
            print(f"📬 Event sent to Kafka topic '{TOPIC_NAME}'")
        except Exception as e:
            print(f"⚠️ Cảnh báo: Lỗi gửi Kafka event ({e}), đơn hàng vẫn tiếp tục xử lý.")
    else:
        print("⚠️ Cảnh báo: Kafka Producer chưa sẵn sàng.")

    return {
        "order_status": "Success",
        "product_name": product_data["name"],
        "total_price": total_price
    }