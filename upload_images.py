"""
upload_images.py
────────────────
Uploads all product images from public/images/ to Supabase Storage
bucket 'product-images', then patches the products table with the
new public CDN URLs.

Usage:
    cd d:\save-sage-site\backend
    python upload_images.py
"""

import sys
import os
import mimetypes
from pathlib import Path
import httpx
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL        = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
BUCKET_NAME         = "product-images"

# Local images directory (relative to the backend folder)
IMAGES_DIR = Path(__file__).parent.parent / "public" / "images"

# Map image filename → product id
PRODUCT_IMAGE_MAP = {
    "kashmiri-chilli.jpg":   "kashmiri-chilli",
    "turmeric-powder.jpg":    "turmeric-powder",
    "garam-masala.jpg":       "garam-masala",
    "cumin-seeds.jpg":        "cumin-seeds",
    "coriander-powder.jpg":   "coriander-powder",
    "cardamom-pods.jpg":      "cardamom-pods",
    "black-pepper.jpg":       "black-pepper",
    "saffron-threads.jpg":    "saffron",
}

AUTH_HEADERS = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
}


def upload_image(client: httpx.Client, filename: str, filepath: Path) -> str | None:
    """Upload a single image to Supabase Storage. Returns public URL on success."""
    mime_type, _ = mimetypes.guess_type(filepath)
    mime_type = mime_type or "image/jpeg"

    storage_path = f"{filename}"  # stored at root of bucket
    upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{storage_path}"

    with open(filepath, "rb") as f:
        image_data = f.read()

    headers = {
        **AUTH_HEADERS,
        "Content-Type": mime_type,
        "x-upsert": "true",  # overwrite if exists
    }

    r = client.post(upload_url, content=image_data, headers=headers)

    if r.status_code in (200, 201):
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{storage_path}"
        return public_url
    else:
        print(f"    ⚠️  Upload failed ({r.status_code}): {r.text[:200]}")
        return None


def update_product_image(client: httpx.Client, product_id: str, image_url: str) -> bool:
    """Update the image_src field of a product in the DB."""
    url = f"{SUPABASE_URL}/rest/v1/products"
    headers = {
        **AUTH_HEADERS,
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    r = client.patch(
        url,
        json={"image_src": image_url},
        params={"id": f"eq.{product_id}"},
        headers=headers,
    )
    return r.status_code in (200, 204)


def ensure_bucket_public(client: httpx.Client):
    """Make sure the bucket exists and is public."""
    # Try to get bucket
    r = client.get(
        f"{SUPABASE_URL}/storage/v1/bucket/{BUCKET_NAME}",
        headers=AUTH_HEADERS,
    )
    if r.status_code == 200:
        print(f"✅ Bucket '{BUCKET_NAME}' exists.")
        return

    # Create bucket as public
    r = client.post(
        f"{SUPABASE_URL}/storage/v1/bucket",
        json={"id": BUCKET_NAME, "name": BUCKET_NAME, "public": True},
        headers={**AUTH_HEADERS, "Content-Type": "application/json"},
    )
    if r.status_code in (200, 201):
        print(f"✅ Created public bucket '{BUCKET_NAME}'.")
    else:
        print(f"⚠️  Could not create bucket: {r.status_code} {r.text[:200]}")


def main():
    print("🖼️  Save Sage Spices — Image Upload to Supabase Storage")
    print("=" * 55)

    if not IMAGES_DIR.exists():
        print(f"❌ Images directory not found: {IMAGES_DIR}")
        sys.exit(1)

    with httpx.Client(timeout=60) as client:
        ensure_bucket_public(client)
        print()

        success_count = 0
        for filename, product_id in PRODUCT_IMAGE_MAP.items():
            filepath = IMAGES_DIR / filename
            if not filepath.exists():
                print(f"  ⚠️  File not found, skipping: {filename}")
                continue

            print(f"  ⬆️  Uploading {filename} ({filepath.stat().st_size // 1024}KB)...")
            public_url = upload_image(client, filename, filepath)

            if public_url:
                ok = update_product_image(client, product_id, public_url)
                status = "✅" if ok else "⚠️  (uploaded but DB update failed)"
                print(f"     {status} {public_url}")
                if ok:
                    success_count += 1
            print()

    print(f"Done! {success_count}/{len(PRODUCT_IMAGE_MAP)} images uploaded and linked.")


if __name__ == "__main__":
    main()
