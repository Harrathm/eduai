from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

r = client.post("/auth/login", data={"username": "admin@demo-academy.edu", "password": "password123"})
assert r.status_code == 200, f"Login failed: {r.text}"
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

tests = [
    ("GET", "/auth/me", None, 200),
    ("GET", "/api/lms/assignments", None, 200),
    ("GET", "/api/lms/classes", None, 200),
    ("GET", "/api/lms/my-classes", None, 200),
    ("GET", "/api/lms/enrollments", None, 200),
    ("GET", "/api/lms/progress", None, 200),
    ("GET", "/api/lms/submissions", None, 200),
    ("GET", "/api/academy/courses", None, 200),
    ("GET", "/api/academy/my-courses", None, 200),
    ("GET", "/api/academy/courses/1/detail", None, 200),
    ("GET", "/api/academy/courses/1/modules", None, 200),
    ("PUT", "/api/academy/courses/1/publish", {"published": True}, 200),
    ("GET", "/api/ai/stats", None, 200),
    ("GET", "/api/ai/usage", None, 200),
    ("GET", "/api/subscriptions/plans", None, 200),
    ("GET", "/api/admin/analytics/overview", None, 200),
    ("GET", "/api/admin/users", None, 200),
]

passed = 0
failed = 0
for method, path, body, expected in tests:
    if method == "GET":
        resp = client.get(path, headers=headers)
    else:
        resp = client.put(path, json=body, headers=headers)
    status = "PASS" if resp.status_code == expected else "FAIL"
    if resp.status_code == expected:
        passed += 1
    else:
        failed += 1
        print(f"{status}: {method} {path} -> {resp.status_code} (expected {expected})")

print(f"\nResults: {passed} passed, {failed} failed")
if failed == 0:
    print("ALL BACKEND ENDPOINTS WORKING!")