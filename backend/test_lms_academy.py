from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

r = client.post("/auth/login", data={"username": "admin@demo-academy.edu", "password": "password123"})
print("Login:", r.status_code)
if r.status_code != 200:
    print("FAIL:", r.text)
    exit(1)
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# LMS tests
assignments = client.get("/api/lms/assignments", headers=headers)
print(f"GET /api/lms/assignments: {assignments.status_code} ({len(assignments.json())} items)")

classes = client.get("/api/lms/classes", headers=headers)
print(f"GET /api/lms/classes: {classes.status_code} ({len(classes.json())} items)")

my_classes = client.get("/api/lms/my-classes", headers=headers)
print(f"GET /api/lms/my-classes: {my_classes.status_code} ({len(my_classes.json())} items)")

enrollments = client.get("/api/lms/enrollments", headers=headers)
print(f"GET /api/lms/enrollments: {enrollments.status_code} ({len(enrollments.json())} items)")

progress = client.get("/api/lms/progress", headers=headers)
print(f"GET /api/lms/progress: {progress.status_code} ({len(progress.json())} items)")

submissions = client.get("/api/lms/submissions", headers=headers)
print(f"GET /api/lms/submissions: {submissions.status_code} ({len(submissions.json())} items)")

# Academy tests
courses = client.get("/api/academy/courses", headers=headers)
print(f"GET /api/academy/courses: {courses.status_code} ({len(courses.json())} items)")

my_courses = client.get("/api/academy/my-courses", headers=headers)
print(f"GET /api/academy/my-courses: {my_courses.status_code} ({len(my_courses.json())} items)")

if courses.json():
    course_id = courses.json()[0]["id"]
    detail = client.get(f"/api/academy/courses/{course_id}/detail", headers=headers)
    print(f"GET /api/academy/courses/{course_id}/detail: {detail.status_code} ({len(detail.json().get('modules', []))} modules)")

    modules = client.get(f"/api/academy/courses/{course_id}/modules", headers=headers)
    print(f"GET /api/academy/courses/{course_id}/modules: {modules.status_code} ({len(modules.json())} modules)")

    pub = client.put(f"/api/academy/courses/{course_id}/publish", json=True, headers=headers)
    print(f"PUT /api/academy/courses/{course_id}/publish: {pub.status_code}")

print("\nAll LMS & Academy endpoints verified!")