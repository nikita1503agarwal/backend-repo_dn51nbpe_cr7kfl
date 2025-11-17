import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product, ContactMessage

app = FastAPI(title="Bakery API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Utilities
class ProductOut(Product):
    id: Optional[str] = None


def serialize_product(doc: dict) -> ProductOut:
    return ProductOut(
        id=str(doc.get("_id")),
        title=doc.get("title"),
        description=doc.get("description"),
        price=float(doc.get("price", 0)),
        category=doc.get("category", ""),
        in_stock=bool(doc.get("in_stock", True)),
        image_url=doc.get("image_url"),
    )


@app.get("/")
def read_root():
    return {"message": "Bakery API is running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# Seed some default bakery products if empty
@app.post("/seed")
def seed_products():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    count = db["product"].count_documents({})
    if count > 0:
        return {"inserted": 0, "message": "Products already exist"}

    items = [
        {
            "title": "Sourdough Loaf",
            "description": "Crusty artisan sourdough with a tender crumb.",
            "price": 6.5,
            "category": "Bread",
            "in_stock": True,
            "image_url": "https://images.unsplash.com/photo-1542838132-92c53300491e?q=80&w=1200&auto=format&fit=crop"
        },
        {
            "title": "Chocolate Croissant",
            "description": "Flaky butter croissant filled with dark chocolate.",
            "price": 3.25,
            "category": "Pastry",
            "in_stock": True,
            "image_url": "https://images.unsplash.com/photo-1547106634-56dcd53ae883?q=80&w=1200&auto=format&fit=crop"
        },
        {
            "title": "Blueberry Muffin",
            "description": "Moist muffin packed with fresh blueberries.",
            "price": 2.95,
            "category": "Muffin",
            "in_stock": True,
            "image_url": "https://images.unsplash.com/photo-1509365465985-25d11c17e812?q=80&w=1200&auto=format&fit=crop"
        },
        {
            "title": "Cinnamon Roll",
            "description": "Swirled with cinnamon, topped with vanilla glaze.",
            "price": 3.5,
            "category": "Pastry",
            "in_stock": True,
            "image_url": "https://images.unsplash.com/photo-1606313564200-e75d5e30476e?q=80&w=1200&auto=format&fit=crop"
        }
    ]

    for item in items:
        create_document("product", item)

    return {"inserted": len(items)}


# Public endpoints
@app.get("/products", response_model=List[ProductOut])
def list_products():
    docs = get_documents("product")
    return [serialize_product(doc) for doc in docs]


class ContactIn(ContactMessage):
    pass


@app.post("/contact")
def send_contact(message: ContactIn):
    create_document("contactmessage", message)
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
