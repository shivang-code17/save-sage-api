"""
seed.py — Seeds the Supabase `products` table using direct HTTP calls.
Usage: python seed.py
"""
import sys
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

PRODUCTS = [
    {"id": "kashmiri-chilli", "name": "Kashmiri Chilli Powder", "price": 250, "weight": "250g pack",
     "rating": 4.8, "review_count": 124, "image_src": "/images/kashmiri-chilli.jpg",
     "category": "powders", "description": "Vibrant red, mild heat with rich color. Perfect for curries and tandoori dishes.",
     "is_bestseller": True, "is_new": False, "stock_quantity": 200},
    {"id": "turmeric-powder", "name": "Organic Turmeric Powder", "price": 180, "weight": "200g pack",
     "rating": 4.9, "review_count": 256, "image_src": "/images/turmeric-powder.jpg",
     "category": "powders", "description": "High curcumin content, stone-ground from Lakadong turmeric roots.",
     "is_bestseller": True, "is_new": False, "stock_quantity": 300},
    {"id": "garam-masala", "name": "Garam Masala Blend", "price": 320, "weight": "150g pack",
     "rating": 4.7, "review_count": 89, "image_src": "/images/garam-masala.jpg",
     "category": "blends", "description": "Traditional North Indian blend with 12 aromatic spices.",
     "is_bestseller": False, "is_new": False, "stock_quantity": 150},
    {"id": "cumin-seeds", "name": "Whole Cumin Seeds", "price": 140, "weight": "200g pack",
     "rating": 4.6, "review_count": 167, "image_src": "/images/cumin-seeds.jpg",
     "category": "whole", "description": "Earthy, nutty flavor. Essential for tempering and dry roasting.",
     "is_bestseller": False, "is_new": False, "stock_quantity": 250},
    {"id": "coriander-powder", "name": "Coriander Powder", "price": 120, "weight": "200g pack",
     "rating": 4.5, "review_count": 98, "image_src": "/images/coriander-powder.jpg",
     "category": "powders", "description": "Fresh, citrusy notes. Freshly ground from whole seeds.",
     "is_bestseller": False, "is_new": True, "stock_quantity": 180},
    {"id": "cardamom-pods", "name": "Green Cardamom Pods", "price": 450, "weight": "100g pack",
     "rating": 4.9, "review_count": 203, "image_src": "/images/cardamom-pods.jpg",
     "category": "whole", "description": "Premium Elettaria pods from Kerala. Intensely aromatic.",
     "is_bestseller": True, "is_new": False, "stock_quantity": 120},
    {"id": "black-pepper", "name": "Tellicherry Black Pepper", "price": 280, "weight": "150g pack",
     "rating": 4.7, "review_count": 145, "image_src": "/images/black-pepper.jpg",
     "category": "whole", "description": "Large, bold peppercorns with complex heat and fruity undertones.",
     "is_bestseller": False, "is_new": False, "stock_quantity": 200},
    {"id": "saffron", "name": "Kashmiri Saffron Threads", "price": 1200, "weight": "2g pack",
     "rating": 5.0, "review_count": 67, "image_src": "/images/saffron-threads.jpg",
     "category": "whole", "description": "Grade A Mongra saffron. Deep red threads with exceptional aroma.",
     "is_bestseller": False, "is_new": True, "stock_quantity": 50},
]


def seed():
    url = f"{SUPABASE_URL}/rest/v1/products"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation,resolution=merge-duplicates",
    }
    print("🌿 Seeding Save Sage Spices products...")
    with httpx.Client() as client:
        r = client.post(url, json=PRODUCTS, params={"on_conflict": "id"}, headers=headers)
        if r.status_code not in (200, 201):
            print(f"❌ Seed failed: {r.status_code} — {r.text}")
            sys.exit(1)
        data = r.json()
        print(f"✅ Seeded {len(data)} products!")
        for p in data:
            print(f"   • {p['id']} — {p['name']} (₹{p['price']})")


if __name__ == "__main__":
    seed()
