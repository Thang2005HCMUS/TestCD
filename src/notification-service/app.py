from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Notification Service")

class NotificationRequest(BaseModel):
    email: str
    message: str

@app.get("/healthz")
def health_check():
    return {"status": "healthy", "service": "notification-service"}

@app.post("/notify")
def send_notification(payload: NotificationRequest):
    # Giả lập logic gửi email thực tế
    print(f"[EMAIL SENT] Gửi tới {payload.email}: {payload.message}")
    return {
        "status": "Sent",
        "to": payload.email
    }