from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings
from routers import products, auth, cart, orders, reviews
import os

settings = get_settings()

app = FastAPI(
    title="Save Sage Spices API",
    description="Backend API for the Save Sage Spices e-commerce platform",
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
origins = [
    "http://localhost:3000",
    os.environ.get("FRONTEND_URL", ""),  # Vercel production URL
]
# Filter out empty strings
origins = [o for o in origins if o]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(auth.router,     prefix="/auth",     tags=["Auth"])
app.include_router(cart.router,     prefix="/cart",     tags=["Cart"])
app.include_router(orders.router,   prefix="/orders",   tags=["Orders"])
app.include_router(reviews.router,  prefix="/reviews",  tags=["Reviews"])


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "app": "Save Sage Spices API", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
