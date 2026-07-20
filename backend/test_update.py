import requests

resp = requests.post('http://localhost:8000/auth/login', data={'username': 'admin@eduai.platform', 'password': 'admin123'})
token = resp.json()['access_token']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

# Test debug ping
resp = requests.get('http://localhost:8000/api/admin/ping-admin', headers=headers)
print('Ping:', resp.status_code, resp.text)

# Test new endpoint
resp = requests.post('http://localhost:8000/api/admin/user-update?user_id=86&is_active=false', headers=headers)
print('Update:', resp.status_code, resp.text)

# Test add tokens
resp = requests.post('http://localhost:8000/api/admin/user-update?user_id=86&token_balance=1500', headers=headers)
print('Add tokens:', resp.status_code, resp.text)

# Test add DT
resp = requests.post('http://localhost:8000/api/admin/user-update?user_id=86&dt_balance=200', headers=headers)
print('Add DT:', resp.status_code, resp.text)

# Test change role to TEACHER
resp = requests.post('http://localhost:8000/api/admin/user-update?user_id=86&role=TEACHER', headers=headers)
print('Change role:', resp.status_code, resp.text)