import requests
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

API_URL = "http://127.0.0.1:8000"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

test_email = "testauth999@example.com"
test_password = "Password123!"

print("Testing Registration...")
res = requests.post(f"{API_URL}/auth/register", json={
    "email": test_email,
    "password": test_password
})

print(f"Register status: {res.status_code}")
if res.status_code == 201:
    print("Registration successful:", res.json())
else:
    print("Registration failed:", res.text)

print("\nTesting Login...")
try:
    response = supabase.auth.sign_in_with_password({
        "email": test_email,
        "password": test_password,
    })
    print("Login successful.")
    print("Session:", response.session is not None)
    print("User ID:", response.user.id)
except Exception as e:
    print("Login failed:", str(e))
