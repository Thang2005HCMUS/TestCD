from fastapi import FastAPI, HTTPException

app = FastAPI(title="Product Service")

# Data giả lập
PRODUCTS = {
    1: {"name": "Laptop Gaming", "price": 1500, "stock": 10},
    2: {"name": "Bàn phím cơ", "price": 100, "stock": 50},
    3: {"name": "Chuột không dây", "price": 50, "stock": 5}
}

@app.get("/healthz")
def health_check():
    return {"status": "healthy", "service": "product-service"}

@app.get("/products")
def get_all_products():
    return list(PRODUCTS.values())

@app.get("/products/{product_id}")
def get_product(product_id: int):
    product = PRODUCTS.get(product_id)
    if not product:#
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
    return product