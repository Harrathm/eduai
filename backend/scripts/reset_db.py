import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.db_utils import get_connection

conn = get_connection(database="postgres")
conn.autocommit = True
cur = conn.cursor()
cur.execute("DROP DATABASE IF EXISTS eduai")
cur.execute("CREATE DATABASE eduai")
conn.close()
print("Database dropped and recreated!")
