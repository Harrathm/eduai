from app.core.security import verify_password, get_password_hash
h = get_password_hash("password123")
print(verify_password('password123', h))