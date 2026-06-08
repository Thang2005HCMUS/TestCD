import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Auth Service")

# Đọc cấu hình từ Environment Variable của K8s
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-default")

class LoginRequest(BaseModel):
    username: str
    password: str

@app.get("/healthz")
def health_check():
    return {"status": "healthy", "service": "auth-service"}

@app.post("/login")
def login(payload: LoginRequest):
    if payload.username == "admin" and payload.password == "password":
        return {
            "access_token": f"mock-token-for-{payload.username}",
            "token_type": "bearer"
        }
    raise HTTPException(status_code=401, detail="Sai tài khoản hoặc mật khẩu")

@app.get("/verify/{token}")
def verify_token(token: str):
    if token.startswith("mock-token-"):
        return {"valid": True, "user": token.replace("mock-token-for-", "")}
    return {"valid": False}