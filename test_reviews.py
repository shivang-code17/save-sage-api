import httpx
import os
from dotenv import load_dotenv

load_dotenv()

db_url = f"{os.environ['SUPABASE_URL']}/rest/v1/reviews"
headers = {
    "apikey": os.environ['SUPABASE_SERVICE_KEY'],
    "Authorization": f"Bearer {os.environ['SUPABASE_SERVICE_KEY']}",
}

# Test without join
print("=== Test 1: Simple reviews select ===")
r1 = httpx.get(db_url, params={"select": "id,rating,body,created_at,user_id", "product_id": "eq.cardamom-pods"}, headers=headers)
print(f"Status: {r1.status_code}")
print(f"Body: {r1.text[:500]}")

# Test with profiles join
print("\n=== Test 2: Reviews with profiles join ===")
r2 = httpx.get(db_url, params={"select": "id,rating,body,created_at,user_id,profiles(full_name)", "product_id": "eq.cardamom-pods"}, headers=headers)
print(f"Status: {r2.status_code}")
print(f"Body: {r2.text[:500]}")

# Test if profiles table exists
print("\n=== Test 3: Profiles table ===")
r3 = httpx.get(f"{os.environ['SUPABASE_URL']}/rest/v1/profiles", params={"select": "*", "limit": "1"}, headers=headers)
print(f"Status: {r3.status_code}")
print(f"Body: {r3.text[:500]}")
