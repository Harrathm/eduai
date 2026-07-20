import sqlite3
import datetime
import random

conn = sqlite3.connect('eduai.db')
cursor = conn.cursor()

# Get user IDs
cursor.execute('SELECT id, email, school_id FROM users')
users = cursor.fetchall()

# Get courses
cursor.execute('SELECT id, author_id FROM courses WHERE status = "PUBLISHED"')
courses = cursor.fetchall()

print("Users:", len(users))
print("Courses:", len(courses))

# Add sample transactions for different schools
transactions = [
    # Demo Academy (school 1)
    (1, 1, 'TOKEN_RECHARGE', 1000, 'TOKEN', 'Token purchase', 'completed'),
    (1, 3, 'COURSE_PURCHASE', 50, 'TOKEN', 'Course: Python Basics', 'completed'),
    (1, 4, 'TOKEN_RECHARGE', 500, 'TOKEN', 'Token purchase', 'completed'),
    (1, 5, 'COURSE_PURCHASE', 50, 'TOKEN', 'Course: Python Basics', 'completed'),
    (1, 6, 'DT_DEPOSIT', 100, 'DT', 'DT deposit', 'completed'),
    (1, 2, 'COURSE_REVENUE', 25, 'DT', 'Course revenue', 'completed'),
    (1, 1, 'TOKEN_RECHARGE', 2000, 'TOKEN', 'Bulk token purchase', 'completed'),
    # Tech Institute (school 2)
    (2, 11, 'TOKEN_RECHARGE', 800, 'TOKEN', 'Token purchase', 'completed'),
    (2, 12, 'COURSE_PURCHASE', 75, 'DT', 'Course: ML', 'completed'),
    # Global University (school 3)
    (3, 16, 'TOKEN_RECHARGE', 600, 'TOKEN', 'Token purchase', 'completed'),
    # Digital Academy (school 4)
    (4, 21, 'TOKEN_RECHARGE', 400, 'TOKEN', 'Token purchase', 'completed'),
]

for school_id, user_id, trans_type, amount, curr, desc, status in transactions:
    cursor.execute('''
        INSERT INTO transactions (school_id, user_id, type, amount, currency, description, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (school_id, user_id, trans_type, amount, curr, desc, status, datetime.datetime.utcnow().isoformat()))

conn.commit()

# Check transactions
cursor.execute('SELECT COUNT(*) FROM transactions')
print("Total transactions:", cursor.fetchone()[0])

conn.close()
print("Done")