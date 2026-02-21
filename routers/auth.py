from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from config import get_db

router = APIRouter()


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(body: SignUpRequest):
    db = get_db()
    try:
        res = db.auth_signup(
            body.email,
            body.password,
            metadata={"full_name": body.full_name or ""},
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    user_id = res.get("id")
    if not user_id:
        raise HTTPException(status_code=400, detail=res.get("msg", "Signup failed"))

    # Create profile row
    try:
        db.upsert("profiles", {"id": user_id, "full_name": body.full_name or ""})
    except Exception:
        pass  # Non-fatal — profile can be created later

    return {
        "message": "User created. Check your email to confirm your account.",
        "user_id": user_id,
        "email": res.get("email"),
    }


@router.post("/login")
async def login(body: SignInRequest):
    db = get_db()
    try:
        res = db.auth_login(body.email, body.password)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

    access_token = res.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = res.get("user", {})
    return {
        "access_token": access_token,
        "refresh_token": res.get("refresh_token"),
        "token_type": "bearer",
        "expires_in": res.get("expires_in"),
        "user": {
            "id": user.get("id"),
            "email": user.get("email"),
            "full_name": (user.get("user_metadata") or {}).get("full_name", ""),
        },
    }


@router.post("/logout")
async def logout():
    return {"message": "Logged out successfully"}
