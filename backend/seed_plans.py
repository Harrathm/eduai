import json
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from app.db_utils import get_connection

conn = get_connection()
cur = conn.cursor()

plans = [
    {
        "name": "Free",
        "price": 0,
        "interval": "month",
        "stripe_price_id": None,
        "active": True,
        "features": json.dumps({
            "students": 10,
            "courses": 3,
            "ai_tutor": True,
            "ai_auto_correct": False,
            "stripe_ai_quizzes": False,
            "custom_content": False,
            "priority_support": False,
        }),
    },
    {
        "name": "Teacher Pro",
        "price": 500,
        "interval": "month",
        "stripe_price_id": "price_teacher_pro",
        "active": True,
        "features": json.dumps({
            "students": 50,
            "courses": 20,
            "ai_tutor": True,
            "ai_auto_correct": True,
            "stripe_ai_quizzes": True,
            "custom_content": True,
            "prioritySupport": False,
        }),
    },
    {
        "name": "School",
        "price": 2900,
        "interval": "month",
        "stripe_price_id": "price_school",
        "active": True,
        "features": json.dumps({
            "students": 500,
            "courses": -1,
            "ai_tutor": True,
            "ai_auto_correct": True,
            "stripe_ai_quizzes": True,
            "custom_content": True,
            "prioritySupport": True,
        }),
    },
    {
        "name": "Institution",
        "price": 9900,
        "interval": "month",
        "stripe_price_id": "price_institution",
        "active": True,
        "features": json.dumps({
            "students": -1,
            "courses": -1,
            "ai_tutor": True,
            "ai_auto_correct": True,
            "stripe_ai_quizzes": True,
            "custom_content": True,
            "prioritySupport": True,
        }),
    },
]

cur.execute("DELETE FROM subscriptions")
conn.commit()
cur.execute("DELETE FROM plans")
conn.commit()

for p in plans:
    cur.execute(
        "INSERT INTO plans (name, price, interval, stripe_price_id, active, features) VALUES (%s, %s, %s, %s, %s, %s)",
        (p["name"], p["price"], p["interval"], p["stripe_price_id"], p["active"], p["features"]),
    )
    conn.commit()
    print(f"Inserted plan: {p['name']}")

cur.execute("SELECT name, price FROM plans ORDER BY price")
for r in cur.fetchall():
    print(f"  Plan: {r[0]} - ${r[1]/100}/month")

conn.close()
print("Plans seeded!")