import os
import asyncio
import json
from fastapi import FastAPI
from pydantic import BaseModel
from aiokafka import AIOKafkaConsumer

app = FastAPI(title="Notification Service")

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-service:9092")
TOPIC_NAME = "order-notifications"

class NotificationRequest(BaseModel):
    email: str
    message: str

@app.get("/healthz")
def health_check():
    return {"status": "healthy", "service": "notification-service"}

@app.post("/notify")
def send_notification(payload: NotificationRequest):
    # Giữ nguyên API cũ để tương thích ngược nếu cần 
    print(f"[API HTTP SENT] Gửi tới {payload.email}: {payload.message}") 
    return {"status": "Sent", "to": payload.email} 

# Hàm chạy ngầm lắng nghe Kafka Event
async def consume_kafka_events():
    while True:
        try:
            consumer = AIOKafkaConsumer(
                TOPIC_NAME,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id="notification-group"
            )
            await consumer.start()
            print(f" 🎧 Kafka Consumer listening on topic '{TOPIC_NAME}'...")
            
            try:
                async for msg in consumer:
                    try:
                        data = json.loads(msg.value.decode('utf-8'))
                        email = data.get("email")
                        message = data.get("message")
                        # Giả lập logic gửi mail thực tế 
                        print(f"[KAFKA EVENT RECEIVED] Gửi tới {email}: {message}")
                    except Exception as parse_err:
                        print(f"❌ Error parsing message: {parse_err}")
            finally:
                await consumer.stop()
        except Exception as conn_err:
            print(f"⚠️ Kafka connection error: {conn_err}. Reconnecting in 5s...")
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    # Chạy Consumer như một background task của Asyncio để không chặn Uvicorn port 8000
    asyncio.create_task(consume_kafka_events())