import requests

# Get current routes from live server via openapi
resp = requests.get('http://localhost:8000/openapi.json')
if resp.ok:
    paths = resp.json().get('paths', {})
    admin_paths = [p for p in paths.keys() if 'admin' in p.lower()]
    for p in admin_paths[:10]:
        methods = list(paths[p].keys())
        print(f"{p} -> {methods}")
else:
    print('OpenAPI not available')

# Test /api/admin/schools (known working)
resp = requests.get('http://localhost:8000/api/admin/schools')
print(f"\n/api/admin/schools: {resp.status_code}")