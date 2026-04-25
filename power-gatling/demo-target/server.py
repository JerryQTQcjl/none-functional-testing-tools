"""Demo target HTTP server for load testing."""

import random
import time
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="LoadForge Demo Target API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PRODUCTS = [
    {"id": i, "name": f"Product {i}", "price": round(random.uniform(10, 1000), 2),
     "category": random.choice(["electronics", "clothing", "food", "toys", "books"]),
     "stock": random.randint(0, 500)}
    for i in range(1, 21)
]

USERS = [
    {"id": i, "name": f"User {i}", "email": f"user{i}@example.com",
     "level": random.choice(["bronze", "silver", "gold", "platinum"])}
    for i in range(1, 51)
]


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "demo-target"}


@app.get("/api/products")
async def list_products():
    time.sleep(random.uniform(0.02, 0.08))
    return {"products": PRODUCTS, "total": len(PRODUCTS)}


@app.get("/api/products/{product_id}")
async def get_product(product_id: int):
    time.sleep(random.uniform(0.01, 0.05))
    for p in PRODUCTS:
        if p["id"] == product_id:
            return p
    raise HTTPException(status_code=404, detail="Product not found")


@app.post("/api/orders")
async def create_order():
    time.sleep(random.uniform(0.05, 0.15))
    product = random.choice(PRODUCTS)
    return {
        "order_id": str(uuid.uuid4()),
        "product_id": product["id"],
        "product_name": product["name"],
        "quantity": random.randint(1, 5),
        "total": round(product["price"] * random.randint(1, 3), 2),
        "status": "created",
    }


@app.get("/api/users")
async def list_users():
    time.sleep(random.uniform(0.02, 0.06))
    return {"users": USERS, "total": len(USERS)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
