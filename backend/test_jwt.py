"""Test JWT token creation and verification"""
import os
os.chdir(r"E:\system_educatif_tn\RAG\RAG_APP_new\backend")

from jose import jwt
from app.core.config import get_settings

settings = get_settings()
secret = settings.jwt_secret
algo = settings.jwt_algorithm

print(f"Secret length: {len(secret)}")
print(f"Algorithm: {algo}")

# Create a test token
from datetime import datetime, timedelta
payload = {"sub": "1", "school_id": 1, "exp": datetime.utcnow() + timedelta(hours=24)}
token = jwt.encode(payload, secret, algorithm=algo)
print(f"Token created: {token[:50]}...")

# Decode it back
decoded = jwt.decode(token, secret, algorithms=[algo])
print(f"Decoded: {decoded}")

# Test with user from DB
from app.db import get_db
from app.models import User
db = next(get_db())
user = db.query(User).first()
if user:
    print(f"User in DB: id={user.id}, email={user.email}, role={user.role}")
    # Create token for this user
    from app.auth import create_access_token
    user_token = create_access_token({"sub": str(user.id), "school_id": user.school_id})
    print(f"User token: {user_token[:50]}...")
    
    # Decode user token
    decoded_user = jwt.decode(user_token, secret, algorithms=[algo])
    print(f"Decoded user token: {decoded_user}")
    
    # Now try to get user by id from token
    user_id = int(decoded_user.get("sub"))
    print(f"User ID from token: {user_id}")
    
    # Query user
    found = db.query(User).filter(User.id == user_id).first()
    print(f"User found in DB: {found}")
else:
    print("No user in DB")