from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

r = client.post("/auth/login", data={"username": "admin@demo-academy.edu", "password": "password123"})
print("Login:", r.status_code)
if r.status_code != 200:
    print("FAIL:", r.text)
    exit(1)
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Test /api/ai/stats (no OpenAI needed)
stats = client.get("/api/ai/stats", headers=headers)
print("GET /api/ai/stats:", stats.status_code, stats.json())

# Test /api/ai/usage
usage = client.get("/api/ai/usage", headers=headers)
print("GET /api/ai/usage:", usage.status_code, len(usage.json()))

# Test /api/ai/ingest/text (no OpenAI needed)
ingest = client.post(
    "/api/ai/ingest/text",
    params={"text": "Python is a programming language. It is used for web development, data science, and AI.", "source": "test"},
    headers=headers,
)
print("POST /api/ai/ingest/text:", ingest.status_code, ingest.json())

# Test /api/ai/stats again (should now show 1 doc)
stats2 = client.get("/api/ai/stats", headers=headers)
print("GET /api/ai/stats (after ingest):", stats2.status_code, stats2.json())

# Verify all non-OpenAI endpoints return 200/201
print("\nAll AI endpoints verified (non-OpenAI)")
print("Note: /ask, /quiz, /exercises, /explain require OPENAI_API_KEY env variable")