from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config import get_db
from dependencies import get_current_user

router = APIRouter()


class ShippingAddress(BaseModel):
    full_name: str
    phone: str
    address_line1: str
    address_line2: str | None = None
    city: str
    state: str
    pincode: str


class CreateOrderRequest(BaseModel):
    shipping_address: ShippingAddress


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_order(body: CreateOrderRequest, user: dict = Depends(get_current_user)):
    db = get_db()

    cart = db.select("carts", columns="id", filters={"user_id": f"eq.{user['id']}"})
    if not cart:
        raise HTTPException(status_code=400, detail="Cart not found or empty")

    cart_id = cart[0]["id"]
    items = db.select(
        "cart_items",
        columns="quantity,product_id,products(id,price,name,stock_quantity)",
        filters={"cart_id": f"eq.{cart_id}"},
    ) or []

    if not items:
        raise HTTPException(status_code=400, detail="Cannot create order from an empty cart")

    total = sum(item["quantity"] * item["products"]["price"] for item in items)

    order = db.insert("orders", {
        "user_id": user["id"],
        "total_amount": round(total, 2),
        "shipping_address": body.shipping_address.model_dump(),
        "status": "pending",
    })
    order_id = order[0]["id"]

    db.insert("order_items", [
        {
            "order_id": order_id,
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "unit_price": item["products"]["price"],
        }
        for item in items
    ])

    db.delete("cart_items", {"cart_id": f"eq.{cart_id}"})

    return {
        "message": "Order placed successfully",
        "order_id": order_id,
        "total_amount": round(total, 2),
        "status": "pending",
    }


@router.get("")
async def list_orders(user: dict = Depends(get_current_user)):
    db = get_db()
    orders = db.select(
        "orders",
        columns="*,order_items(*,products(id,name,image_src))",
        filters={"user_id": f"eq.{user['id']}"},
        order="created_at.desc",
    ) or []
    return {"orders": orders}


@router.get("/{order_id}")
async def get_order(order_id: str, user: dict = Depends(get_current_user)):
    db = get_db()
    order = db.select(
        "orders",
        columns="*,order_items(*,products(id,name,price,image_src,weight))",
        filters={"id": f"eq.{order_id}", "user_id": f"eq.{user['id']}"},
        single=True,
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
