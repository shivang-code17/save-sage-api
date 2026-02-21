from fastapi import APIRouter, Query, HTTPException
from config import get_db
from typing import Literal

router = APIRouter()


@router.get("")
async def list_products(
    category: str | None = Query(None),
    search: str | None = Query(None),
    sort: Literal["featured", "newest", "price_asc", "price_desc", "rating"] = Query("featured"),
):
    db = get_db()

    filters: dict = {}
    if category and category != "all":
        filters["category"] = f"eq.{category}"
    if search:
        filters["or"] = f"(name.ilike.%{search}%,description.ilike.%{search}%)"

    products = db.select("products", filters=filters or None)
    products = products or []

    # Sort
    if sort == "featured":
        products.sort(key=lambda p: (not p.get("is_bestseller"), p.get("name", "")))
    elif sort == "newest":
        products.sort(key=lambda p: not p.get("is_new"))
    elif sort == "price_asc":
        products.sort(key=lambda p: p.get("price", 0))
    elif sort == "price_desc":
        products.sort(key=lambda p: p.get("price", 0), reverse=True)
    elif sort == "rating":
        products.sort(key=lambda p: p.get("rating", 0), reverse=True)

    return {"products": products, "count": len(products)}


@router.get("/{product_id}")
async def get_product(product_id: str):
    db = get_db()
    product = db.select("products", filters={"id": f"eq.{product_id}"}, single=True)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found")
    return product
