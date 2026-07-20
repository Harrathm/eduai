from app.core.security import verify_password
h = "$2b$12$PiO0X8xHJ2SynXHUmp57neoRBzPpWJgZ2c6MpwXSlgtF3dyzWTQDa"
print(verify_password('password123', h))