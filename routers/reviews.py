from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config import get_db
from dependencies import get_current_user, get_optional_user

router = APIRouter()


class ReviewRequest(BaseModel):
    rating: int
    body: str | None = None


@router.get("/{product_id}")
async def list_reviews(product_id: str, user: dict | None = Depends(get_optional_user)):
    db = get_db()
    prod = db.select("products", columns="id,rating,review_count", filters={"id": f"eq.{product_id}"})
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    reviews = db.select(
        "reviews",
        columns="id,rating,body,created_at,user_id,profiles(full_name)",
        filters={"product_id": f"eq.{product_id}"},
        order="created_at.desc",
    ) or []

    if user:
        for r in reviews:
            r["is_mine"] = r["user_id"] == user["id"]

    return {
        "product_id": product_id,
        "average_rating": prod[0]["rating"],
        "review_count": prod[0]["review_count"],
        "reviews": reviews,
    }


@router.post("/{product_id}", status_code=status.HTTP_201_CREATED)
async def post_review(product_id: str, body: ReviewRequest, user: dict = Depends(get_current_user)):
    if not (1 <= body.rating <= 5):
        raise HTTPException(status_code=422, detail="Rating must be between 1 and 5")

    db = get_db()
    prod = db.select("products", columns="id", filters={"id": f"eq.{product_id}"})
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = db.select("reviews", columns="id",
                         filters={"product_id": f"eq.{product_id}", "user_id": f"eq.{user['id']}"})
    if existing:
        raise HTTPException(status_code=409, detail="You have already reviewed this product")

    review = db.insert("reviews", {
        "product_id": product_id,
        "user_id": user["id"],
        "rating": body.rating,
        "body": body.body,
    })
    return {"message": "Review submitted", "review": review[0]}


@router.delete("/{review_id}")
async def delete_review(review_id: str, user: dict = Depends(get_current_user)):
    db = get_db()
    review = db.select("reviews", columns="id,user_id", filters={"id": f"eq.{review_id}"})
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review[0]["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Cannot delete another user's review")
    db.delete("reviews", {"id": f"eq.{review_id}"})
    return {"message": "Review deleted"}
