import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.db_utils import get_connection

# Connect directly to postgres DB to reset eduai DB
conn = get_connection(database="postgres")
conn.autocommit = True
cur = conn.cursor()

print("Dropping and recreating eduai database...")

cur.execute("DROP DATABASE IF EXISTS eduai")
cur.execute("CREATE DATABASE eduai")
conn.close()
print("Database eduai recreated!")

# Now connect to eduai and create tables
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+pg8000://postgres:@localhost:5432/eduai")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
db = Session()

print("Creating tables...")

# Create tables
db.execute(text("""
    CREATE TABLE IF NOT EXISTS schools (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        slug VARCHAR(255) UNIQUE NOT NULL,
        description TEXT,
        website VARCHAR(255),
        address TEXT,
        email VARCHAR(255),
        phone VARCHAR(255),
        is_active BOOLEAN DEFAULT true,
        plan VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        domain VARCHAR(255)
    )
"""))

db.execute(text("""
    CREATE TABLE IF NOT EXISTS plans (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        price INTEGER NOT NULL,
        interval VARCHAR(20) DEFAULT 'month'
    )
"""))

db.execute(text("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        hashed_password VARCHAR(255) NOT NULL,
        full_name VARCHAR(255),
        is_active BOOLEAN DEFAULT true,
        role VARCHAR(50) DEFAULT 'student',
        school_id INTEGER REFERENCES schools(id)
    )
"""))

db.execute(text("""
    CREATE TABLE IF NOT EXISTS classes (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        school_id INTEGER REFERENCES schools(id)
    )
"""))

db.execute(text("""
    CREATE TABLE IF NOT EXISTS courses (
        id SERIAL PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        school_id INTEGER REFERENCES schools(id)
    )
"""))

db.execute(text("""
    CREATE TABLE IF NOT EXISTS modules (
        id SERIAL PRIMARY KEY,
        course_id INTEGER REFERENCES courses(id),
        title VARCHAR(255) NOT NULL,
        "order" INTEGER DEFAULT 0,
        school_id INTEGER REFERENCES schools(id)
    )
"""))

db.execute(text("""
    CREATE TABLE IF NOT EXISTS lessons (
        id SERIAL PRIMARY KEY,
        module_id INTEGER REFERENCES modules(id),
        title VARCHAR(255) NOT NULL,
        content TEXT,
        "order" INTEGER DEFAULT 0,
        school_id INTEGER REFERENCES schools(id)
    )
"""))

db.execute(text("""
    CREATE TABLE IF NOT EXISTS quizzes (
        id SERIAL PRIMARY KEY,
        lesson_id INTEGER REFERENCES lessons(id),
        title VARCHAR(255) NOT NULL,
        questions TEXT,
        school_id INTEGER REFERENCES schools(id)
    )
"""))

db.execute(text("""
    CREATE TABLE IF NOT EXISTS assignments (
        id SERIAL PRIMARY KEY,
        class_id INTEGER REFERENCES classes(id),
        title VARCHAR(255) NOT NULL,
        description TEXT,
        due_date TIMESTAMP,
        school_id INTEGER REFERENCES schools(id)
    )
"""))

db.execute(text("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        id SERIAL PRIMARY KEY,
        plan_id INTEGER REFERENCES plans(id),
        school_id INTEGER REFERENCES schools(id),
        status VARCHAR(50) DEFAULT 'active',
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ends_at TIMESTAMP
    )
"""))

db.commit()
print("[OK] Tables created")

# Now seed data
print("\nSeeding data...")

# Schools
db.execute(text("""
    INSERT INTO schools (name, slug, description, website, email, is_active, plan)
    VALUES 
    ('Demo Academy', 'demo-academy.edu', 'A premier online learning platform', 'https://demo-academy.edu', 'admin@demo-academy.edu', true, 'pro'),
    ('Tech Institute', 'tech-institute.edu', 'Advanced technical training institute', 'https://tech-institute.edu', 'director@tech-institute.edu', true, 'school'),
    ('Global University Online', 'global-university.edu', 'World-class online university', 'https://global-university.edu', 'info@global-university.edu', true, 'institution')
"""))
db.commit()

# Plans
db.execute(text("""
    INSERT INTO plans (name, price, interval) VALUES 
    ('Basic', 0, 'month'),
    ('Teacher Pro', 500, 'month'),
    ('School', 2900, 'month'),
    ('Institution', 9900, 'month')
"""))
db.commit()

# Users (password123 hash)
from app.core.security import get_password_hash
password_hash = get_password_hash("password123")

db.execute(text(f"""
    INSERT INTO users (email, hashed_password, full_name, role, school_id, is_active)
    VALUES 
    ('admin@demo-academy.edu', '{password_hash}', 'Admin User', 'admin', 1, true),
    ('teacher@demo-academy.edu', '{password_hash}', 'John Smith', 'teacher', 1, true),
    ('teacher2@demo-academy.edu', '{password_hash}', 'Sarah Johnson', 'teacher', 1, true),
    ('student@demo-academy.edu', '{password_hash}', 'Alice Brown', 'student', 1, true),
    ('student2@demo-academy.edu', '{password_hash}', 'Bob Wilson', 'student', 1, true),
    ('student3@demo-academy.edu', '{password_hash}', 'Carol Davis', 'student', 1, true),
    ('director@tech-institute.edu', '{password_hash}', 'Michael Chen', 'admin', 2, true),
    ('professor@tech-institute.edu', '{password_hash}', 'Emily Rodriguez', 'teacher', 2, true),
    ('learner@tech-institute.edu', '{password_hash}', 'David Kim', 'student', 2, true),
    ('admin@global-university.edu', '{password_hash}', 'Dr. Amanda White', 'admin', 3, true),
    ('instructor@global-university.edu', '{password_hash}', 'Prof. James Taylor', 'teacher', 3, true),
    ('online@global-university.edu', '{password_hash}', 'Lisa Anderson', 'student', 3, true)
"""))
db.commit()

# Classes
db.execute(text("""
    INSERT INTO classes (name, school_id) VALUES 
    ('Python 101', 1), ('Web Development Bootcamp', 1), ('Data Science Fundamentals', 1), ('Advanced JavaScript', 1),
    ('Machine Learning Basics', 2), ('Cloud Computing', 2), ('Computer Science 101', 3), ('Advanced AI', 3)
"""))
db.commit()

# Courses
db.execute(text("""
    INSERT INTO courses (title, description, school_id) VALUES 
    ('Introduction to Python Programming', 'Learn Python from scratch', 1),
    ('Web Development with FastAPI', 'Build modern web apps', 1),
    ('Data Science Fundamentals', 'Data analysis and visualization', 1),
    ('Advanced JavaScript', 'Master modern JS ES6+', 1),
    ('Machine Learning Fundamentals', 'ML algorithms', 2),
    ('Cloud Computing with AWS', 'Deploy on AWS', 2),
    ('Computer Science 101', 'CS fundamentals', 3),
    ('Advanced AI and Deep Learning', 'Neural networks', 3)
"""))
db.commit()

# Modules
db.execute(text("""
    INSERT INTO modules (course_id, title, school_id) VALUES 
    (1, 'Getting Started with Python', 1), (1, 'Variables and Data Types', 1), (1, 'Control Flow', 1), (1, 'Functions', 1), (1, 'Working with Files', 1),
    (2, 'FastAPI Basics', 1), (2, 'RESTful APIs', 1), (2, 'Database Integration', 1), (2, 'Authentication', 1),
    (3, 'Intro to Data Science', 1), (3, 'Data Visualization', 1), (3, 'Statistical Analysis', 1),
    (5, 'ML Fundamentals', 2), (5, 'Supervised Learning', 2), (5, 'Unsupervised Learning', 2),
    (7, 'Algorithms 101', 3), (7, 'Data Structures', 3), (8, 'Neural Networks', 3), (8, 'Deep Learning', 3)
"""))
db.commit()

# Lessons
db.execute(text("""
    INSERT INTO lessons (module_id, title, content, school_id) VALUES 
    (1, 'Installation', '## Installing Python\n\nDownload Python from python.org', 1),
    (1, 'Hello World', '## Your First Python Program\n\n```python\nprint("Hello, World!")\n```', 1),
    (1, 'Setting Up IDE', '## IDE Setup\n\nWe recommend VS Code', 1),
    (2, 'Variables', '## Variables\n\nVariables are containers', 1),
    (2, 'Data Types', '## Data Types\n\nStrings, integers, floats', 1),
    (2, 'Type Conversion', '## Type Conversion', 1),
    (3, 'If Statements', '## Conditional Statements\n\nUse if, elif, else', 1),
    (3, 'For Loops', '## For Loops\n\nIterate over sequences', 1),
    (3, 'While Loops', '## While Loops', 1),
    (4, 'Functions', '## Functions', 1),
    (4, 'Parameters', '## Function Parameters', 1),
    (4, 'Return Values', '## Return Values', 1),
    (6, 'FastAPI Intro', '## FastAPI Introduction', 1),
    (6, 'Routes', '## Creating Routes', 1),
    (7, 'Request Methods', '## HTTP Methods', 1),
    (10, 'What is Data Science?', '## Data Science Overview', 1),
    (13, 'ML Introduction', '## Machine Learning', 2),
    (17, 'Big O Notation', '## Algorithm Complexity', 3),
    (18, 'Neural Networks', '## Neural Networks', 3)
"""))
db.commit()

# Quizzes
db.execute(text("""
    INSERT INTO quizzes (lesson_id, title, questions, school_id) VALUES 
    (1, 'Python Installation Quiz', '[{"question": "What is Python?", "options": ["A snake", "A language", "An OS", "A database"], "answer": "B"}]', 1),
    (4, 'Variables Quiz', '[{"question": "How do you create a variable?", "options": ["var x = 5", "x = 5", "let x = 5", "int x = 5"], "answer": "B"}]', 1),
    (7, 'Control Flow Quiz', '[{"question": "Which keyword starts a condition?", "options": ["for", "if", "loop", "when"], "answer": "B"}]', 1),
    (13, 'FastAPI Quiz', '[{"question": "What is FastAPI?", "options": ["Database", "Web framework", "OS", "Language"], "answer": "B"}]', 1)
"""))
db.commit()

# Assignments
db.execute(text("""
    INSERT INTO assignments (class_id, title, description, due_date, school_id) VALUES 
    (1, 'Hello World Program', 'Write a program that prints Hello World', NOW() + INTERVAL '7 days', 1),
    (1, 'Calculator', 'Build a simple calculator', NOW() + INTERVAL '14 days', 1),
    (1, 'Temperature Converter', 'Convert Celsius to Fahrenheit', NOW() + INTERVAL '21 days', 1),
    (2, 'Create Your First API', 'Build a REST API', NOW() + INTERVAL '10 days', 1),
    (2, 'Database Integration', 'Connect API to database', NOW() + INTERVAL '20 days', 1),
    (3, 'Data Analysis Project', 'Analyze the dataset', NOW() + INTERVAL '14 days', 1),
    (5, 'ML Model', 'Build a linear regression model', NOW() + INTERVAL '21 days', 2)
"""))
db.commit()

# Subscriptions
db.execute(text("""
    INSERT INTO subscriptions (plan_id, school_id, status, started_at, ends_at) VALUES 
    (2, 1, 'active', NOW(), NOW() + INTERVAL '30 days'),
    (3, 2, 'active', NOW(), NOW() + INTERVAL '30 days'),
    (4, 3, 'active', NOW(), NOW() + INTERVAL '30 days')
"""))
db.commit()

print("[OK] All data seeded!")

# Show counts
print("\n" + "="*50)
print("DATABASE SEED COMPLETE!")
print("="*50)

counts = {
    "Schools": db.execute(text("SELECT COUNT(*) FROM schools")).scalar(),
    "Plans": db.execute(text("SELECT COUNT(*) FROM plans")).scalar(),
    "Users": db.execute(text("SELECT COUNT(*) FROM users")).scalar(),
    "Classes": db.execute(text("SELECT COUNT(*) FROM classes")).scalar(),
    "Courses": db.execute(text("SELECT COUNT(*) FROM courses")).scalar(),
    "Modules": db.execute(text("SELECT COUNT(*) FROM modules")).scalar(),
    "Lessons": db.execute(text("SELECT COUNT(*) FROM lessons")).scalar(),
    "Quizzes": db.execute(text("SELECT COUNT(*) FROM quizzes")).scalar(),
    "Assignments": db.execute(text("SELECT COUNT(*) FROM assignments")).scalar(),
    "Subscriptions": db.execute(text("SELECT COUNT(*) FROM subscriptions")).scalar(),
}

for table, count in counts.items():
    print(f"  {table}: {count}")

print("\nLOGIN CREDENTIALS (password: password123)")
print("-"*50)
print("  Admin:   admin@demo-academy.edu")
print("  Teacher: teacher@demo-academy.edu")  
print("  Student: student@demo-academy.edu")
print("  School 2: director@tech-institute.edu")
print("  School 3: admin@global-university.edu")
print("="*50)

db.close()