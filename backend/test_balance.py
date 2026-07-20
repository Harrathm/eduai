import requests

resp = requests.post('http://localhost:8000/auth/login', data={'username': 'admin@eduai.platform', 'password': 'admin123'})
token = resp.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

resp = requests.get('http://localhost:8000/api/admin/users', headers=headers)
users = resp.json()

for u in users:
    if u['id'] == 86:
        print(f"User 86 BEFORE: dt={u['dt_balance']}, tokens={u['token_balance']}")
        break

resp = requests.post('http://localhost:8000/api/admin/wallets/86/add?amount_tokens=100', 
                    headers=headers, json={'reason': 'test add tokens'})
print(f"Add tokens response: {resp.status_code} - {resp.text}")

resp = requests.get('http://localhost:8000/api/admin/users', headers=headers)
users = resp.json()

for u in users:
    if u['id'] == 86:
        print(f"User 86 AFTER: dt={u['dt_balance']}, tokens={u['token_balance']}")
        break