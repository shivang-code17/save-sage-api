from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config import get_db
from dependencies import get_current_user

router = APIRouter()


class AddItemRequest(BaseModel):
    product_id: str
    quantity: int = 1


class UpdateQuantityRequest(BaseModel):
    quantity: int


def _get_or_create_cart(user_id: str) -> str:
    db = get_db()
    rows = db.select("carts", columns="id", filters={"user_id": f"eq.{user_id}"})
    if rows:
        return rows[0]["id"]
    new_cart = db.insert("carts", {"user_id": user_id})
    return new_cart[0]["id"]


def _build_cart_response(cart_id: str) -> dict:
    db = get_db()
    items = db.select(
        "cart_items",
        columns="id,quantity,product_id,products(id,name,price,weight,image_src,category)",
        filters={"cart_id": f"eq.{cart_id}"},
    ) or []
    total = sum(
        item["quantity"] * item["products"]["price"]
        for item in items
        if item.get("products")
    )
    return {"cart_id": cart_id, "items": items, "total": round(total, 2), "item_count": len(items)}


@router.get("")
async def get_cart(user: dict = Depends(get_current_user)):
    cart_id = _get_or_create_cart(user["id"])
    return _build_cart_response(cart_id)


@router.post("/items", status_code=status.HTTP_201_CREATED)
async def add_item(body: AddItemRequest, user: dict = Depends(get_current_user)):
    db = get_db()
    cart_id = _get_or_create_cart(user["id"])

    prod = db.select("products", columns="id,stock_quantity", filters={"id": f"eq.{body.product_id}"})
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = db.select("cart_items", columns="id,quantity",
                         filters={"cart_id": f"eq.{cart_id}", "product_id": f"eq.{body.product_id}"})
    if existing:
        item = existing[0]
        db.update("cart_items", {"quantity": item["quantity"] + body.quantity},
                  {"id": f"eq.{item['id']}"})
    else:
        db.insert("cart_items", {"cart_id": cart_id, "product_id": body.product_id, "quantity": body.quantity})

    return _build_cart_response(cart_id)


@router.patch("/items/{item_id}")
async def update_item(item_id: str, body: UpdateQuantityRequest, user: dict = Depends(get_current_user)):
    db = get_db()
    cart_id = _get_or_create_cart(user["id"])
    if body.quantity <= 0:
        db.delete("cart_items", {"id": f"eq.{item_id}", "cart_id": f"eq.{cart_id}"})
    else:
        db.update("cart_items", {"quantity": body.quantity}, {"id": f"eq.{item_id}", "cart_id": f"eq.{cart_id}"})
    return _build_cart_response(cart_id)


@router.delete("/items/{item_id}")
async def remove_item(item_id: str, user: dict = Depends(get_current_user)):
    db = get_db()
    cart_id = _get_or_create_cart(user["id"])
    db.delete("cart_items", {"id": f"eq.{item_id}", "cart_id": f"eq.{cart_id}"})
    return _build_cart_response(cart_id)


@router.delete("")
async def clear_cart(user: dict = Depends(get_current_user)):
    db = get_db()
    cart_id = _get_or_create_cart(user["id"])
    db.delete("cart_items", {"cart_id": f"eq.{cart_id}"})
    return {"message": "Cart cleared", "cart_id": cart_id, "items": [], "total": 0, "item_count": 0}
