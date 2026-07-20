from app.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Check modules table columns
    result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='modules'"))
    print("Modules columns:", [row[0] for row in result])
    
    # Check lessons table columns
    result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='lessons'"))
    print("Lessons columns:", [row[0] for row in result])