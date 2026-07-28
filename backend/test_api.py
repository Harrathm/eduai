import requests

BASE = "http://localhost:8000"

# Login
resp = requests.post(f"{BASE}/auth/login", data={"username": "admin@eduai.platform", "password": "password123"})
print("Login:", resp.status_code)
token = resp.json()["access_token"]

# Test /auth/me
resp = requests.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {token}"})
print("/auth/me:", resp.status_code, resp.json() if resp.ok else resp.text)

# Test admin users
resp = requests.get(f"{BASE}/api/admin/users", headers={"Authorization": f"Bearer {token}"})
print("/api/admin/users:", resp.status_code)
if resp.ok:
    print("  Users:", len(resp.json()))
else:
    print("  Error:", resp.text[:200])