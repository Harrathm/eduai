from app.main import app
print(f"Total routes: {len(app.routes)}")
for r in app.routes:
    path = getattr(r, "path", "")
    methods = getattr(r, "methods", set())
    if "teacher" in str(path).lower() and "reg" not in str(path).lower():
        print(f"  {methods} {path}")
