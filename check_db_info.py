from sqlalchemy import create_engine, text
e = create_engine("postgresql+pg8000://postgres:gill4264@localhost:5432/eduai")
c = e.connect()
r = c.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users'"))
print("User columns:", [dict(row._mapping)["column_name"] for row in r])
r2 = c.execute(text("SELECT DISTINCT category FROM courses WHERE category IS NOT NULL"))
print("Course categories:", [dict(row._mapping)["category"] for row in r2])
c.close()
