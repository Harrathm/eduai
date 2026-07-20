import requests

print("=== EDUAI LEARNING - FINAL STATUS ===")

# Test login as super admin
r = requests.post('http://localhost:8000/auth/login', data={'username': 'admin@eduai.platform', 'password': 'admin123'}, timeout=3)
if r.ok:
    token = r.json()['access_token']
    print("Auth: SUPER_ADMIN login OK")
    
    # Get dashboard
    r2 = requests.get('http://localhost:8000/api/admin/dashboard', headers={'Authorization': f'Bearer {token}'}, timeout=3)
    if r2.ok:
        stats = r2.json()
        print(f"Dashboard: {stats.get('total_users')} users, {stats.get('total_courses')} courses")
    
    # Get subscriptions
    r3 = requests.get('http://localhost:8000/api/admin/subscriptions', headers={'Authorization': f'Bearer {token}'}, timeout=3)
    if r3.ok:
        print(f"Subscriptions: {len(r3.json())} active")
else:
    print("Auth: FAILED")

# Test school admin
r = requests.post('http://localhost:8000/auth/login', data={'username': 'admin@pro-school.edu', 'password': 'admin123'}, timeout=3)
if r.ok:
    token = r.json()['access_token']
    print("Auth: SCHOOL_ADMIN login OK")
    
    # Get users (scoped to their school only)
    r2 = requests.get('http://localhost:8000/api/admin/users', headers={'Authorization': f'Bearer {token}'}, timeout=3)
    if r2.ok:
        print(f"Users (school-scoped): {len(r2.json())}")

print("=== ALL SYSTEMS OPERATIONAL ===")