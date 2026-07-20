import sys
sys.path.insert(0, '.')

from app.db import get_db
from app.models import User, Course, Transaction, TeacherRegistration

db_gen = get_db()
db = next(db_gen)

school_id = 1

try:
    total_users = db.query(User).filter(User.school_id == school_id).count()
    print(f"total_users: {total_users}")
except Exception as e:
    print(f"Error total_users: {e}")

try:
    total_courses = db.query(Course).filter(Course.school_id == school_id).count()
    print(f"total_courses: {total_courses}")
except Exception as e:
    print(f"Error total_courses: {e}")

try:
    courses = db.query(Course).filter(Course.school_id == school_id).all()
    print(f"Course count: {len(courses)}")
    for c in courses[:3]:
        print(f"  - {c.title}, status={c.status}, price_tokens={c.price_tokens}")
except Exception as e:
    print(f"Error courses: {e}")