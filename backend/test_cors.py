import requests

url = "http://localhost:8000/api/admin/dashboard"
headers = {"Origin": "http://localhost:5173", "Authorization": "Bearer test"}

try:
    r = requests.get(url, headers=headers, timeout=3)
    print("Status:", r.status_code)
    print("Headers:", dict(r.headers))
except Exception as e:
    print("Error:", e)
    
# Try preflight
r = requests.options(url, headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"}, timeout=3)
print("Preflight Status:", r.status_code)
print("Preflight Headers:", dict(r.headers))