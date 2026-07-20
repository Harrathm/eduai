import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from app.db_utils import get_connection

conn = get_connection()
conn.autocommit = True
cursor = conn.cursor()

# Schools - check and add missing columns
print("=== Schools Table ===")
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'schools'")
school_cols = {row[0] for row in cursor.fetchall()}
print(f"Current: {sorted(school_cols)}")

# Add missing columns to schools
missing_school_cols = [
    ("subscription_tier", "VARCHAR(50) DEFAULT 'FREE'"),
    ("max_students", "INTEGER DEFAULT 10"),
    ("max_teachers", "INTEGER DEFAULT 3"),
    ("max_courses", "INTEGER DEFAULT 5"),
    ("max_storage_mb", "INTEGER DEFAULT 100"),
    ("features", "JSONB DEFAULT '{}'::jsonb"),
]
for col, typ in missing_school_cols:
    if col not in school_cols:
        try:
            cursor.execute(f"ALTER TABLE schools ADD COLUMN {col} {typ}")
            print(f"Added {col}")
        except Exception as e:
            print(f"{col}: {e}")

# Courses - check and add
print("\n=== Courses Table ===")
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'courses'")
course_cols = {row[0] for row in cursor.fetchall()}
print(f"Current: {sorted(course_cols)}")

missing_course_cols = [
    ("author_id", "INTEGER REFERENCES users(id)"),
    ("title", "VARCHAR(255)"),
    ("description", "TEXT"),
    ("thumbnail_url", "VARCHAR(500)"),
    ("price", "INTEGER DEFAULT 0"),
    ("is_published", "BOOLEAN DEFAULT FALSE"),
    ("category", "VARCHAR(100)"),
    ("level", "VARCHAR(50) DEFAULT 'BEGINNER'"),
    ("duration_hours", "INTEGER DEFAULT 0"),
    ("language", "VARCHAR(50) DEFAULT 'en'"),
    ("is_free", "BOOLEAN DEFAULT TRUE"),
]
for col, typ in missing_course_cols:
    if col not in course_cols:
        try:
            cursor.execute(f"ALTER TABLE courses ADD COLUMN {col} {typ}")
            print(f"Added {col}")
        except Exception as e:
            print(f"{col}: {e}")

# Course enrollments
print("\n=== Course Enrollments Table ===")
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'course_enrollments'")
enroll_cols = {row[0] for row in cursor.fetchall()}
print(f"Current: {sorted(enroll_cols)}")

# Transactions
print("\n=== Transactions Table ===")
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'transactions'")
trans_cols = {row[0] for row in cursor.fetchall()}
print(f"Current: {sorted(trans_cols)}")

# Verify final
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'schools'")
print(f"\n=== Updated Schools ===")
print([row[0] for row in cursor.fetchall()])