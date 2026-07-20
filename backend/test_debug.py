import requests
import json

BASE = "http://localhost:8000"

# Step 1: Login
print("=== Step 1: Login ===")
resp = requests.post(f"{BASE}/auth/login", data={"username": "admin@eduai.platform", "password": "admin123"})
print(f"Status: {resp.status_code}")
if resp.status_code != 200:
    print(f"Error: {resp.text}")
    exit(1)
    
token = resp.json()["access_token"]
print(f"Token: {token[:30]}...")

# Step 2: Get current user
print("\n=== Step 2: Get /auth/me ===")
resp = requests.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {token}"})
print(f"Status: {resp.status_code}")
if resp.status_code != 200:
    print(f"Error: {resp.text}")
    exit(1)
    
user_data = resp.json()
print(f"User: id={user_data['id']}, email={user_data['email']}, role={user_data['role']}")

# Step 3: Try to access admin endpoint directly with the token
print("\n=== Step 3: Direct admin access ===")
headers = {"Authorization": f"Bearer {token}"}

# First check if /api/admin exists
resp = requests.get(f"{BASE}/api/admin", headers=headers)
print(f"/api/admin: {resp.status_code}")

# Then try users
resp = requests.get(f"{BASE}/api/admin/users", headers=headers)
print(f"/api/admin/users: {resp.status_code}")
if resp.status_code != 200:
    print(f"  Error: {resp.text}")

# Check what the user object looks like from the database
print("\n=== User from DB ===")
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from app.db_utils import get_connection
conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT id, email, role, school_id FROM users WHERE email = 'admin@eduai.platform'")
user = cursor.fetchone()
print(f"DB User: id={user[0]}, email={user[1]}, role={user[2]}, school_id={user[3]}")
conn.close()