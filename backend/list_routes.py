from app.main import app
import sys

for route in app.routes:
    if hasattr(route, 'path') and 'admin' in route.path.lower():
        methods = list(route.methods) if hasattr(route, 'methods') else []
        sys.stdout.write(f"{route.path} -> {methods}\n")