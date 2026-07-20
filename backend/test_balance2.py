import requests

resp = requests.post('http://localhost:8000/auth/login', data={'username': 'admin@eduai.platform', 'password': 'admin123'})
token = resp.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Check user 91 before
resp = requests.get('http://localhost:8000/api/admin/users', headers=headers)
for u in resp.json():
    if u['id'] == 91:
        print(f"User 91 BEFORE: dt={u['dt_balance']}, tokens={u['token_balance']}")
        break

# Test add tokens via query params (like frontend does)
import urllib.parse
url = 'http://localhost:8000/api/admin/wallets/91/add'
params = {'amount_tokens': 25}
full_url = f"{url}?{urllib.parse.urlencode(params)}"
resp = requests.post(full_url, headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}, json={'reason': 'test frontend'})
print(f"Response: {resp.status_code}")
print(f"Body: {resp.text}")

# Check after
resp = requests.get('http://localhost:8000/api/admin/users', headers=headers)
for u in resp.json():
    if u['id'] == 91:
        print(f"User 91 AFTER: dt={u['dt_balance']}, tokens={u['token_balance']}")
        break