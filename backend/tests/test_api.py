"""
Tests for admin_courses router.
"""

import pytest


class TestAdminCourses:
    """Admin course management tests."""

    def test_list_courses_requires_auth(self, client):
        r = client.get("/api/admin/courses")
        assert r.status_code == 401

    def test_list_courses_with_admin(self, client, admin_token):
        r = client.get(
            "/api/admin/courses",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_create_course(self, client, admin_token):
        r = client.post(
            "/api/admin/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Test Course", "level": "beginner"}
        )
        assert r.status_code == 201
        data = r.json()
        assert data["title"] == "Test Course"
        assert data["status"] == "draft"
        assert data["id"] > 0

    def test_create_course_validates_title(self, client, admin_token):
        r = client.post(
            "/api/admin/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": ""}
        )
        assert r.status_code == 422

    def test_get_course(self, client, admin_token):
        create_r = client.post(
            "/api/admin/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "My Course", "level": "intermediate"}
        )
        course_id = create_r.json()["id"]

        r = client.get(
            f"/api/admin/courses/{course_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert r.status_code == 200
        assert r.json()["title"] == "My Course"

    def test_get_course_not_found(self, client, admin_token):
        r = client.get(
            "/api/admin/courses/99999",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert r.status_code == 404

    def test_update_course(self, client, admin_token):
        create_r = client.post(
            "/api/admin/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Original Title"}
        )
        course_id = create_r.json()["id"]

        r = client.patch(
            f"/api/admin/courses/{course_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Updated Title", "level": "advanced"}
        )
        assert r.status_code == 200
        assert r.json()["title"] == "Updated Title"
        assert r.json()["level"] == "advanced"

    def test_delete_course(self, client, admin_token):
        create_r = client.post(
            "/api/admin/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "To Delete"}
        )
        course_id = create_r.json()["id"]

        r = client.delete(
            f"/api/admin/courses/{course_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert r.status_code == 204

        r2 = client.get(
            f"/api/admin/courses/{course_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert r2.status_code == 404

    def test_publish_course(self, client, admin_token):
        # Create course with required fields
        create_r = client.post(
            "/api/admin/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Publish Me", "level": "beginner", "short_description": "A test course"}
        )
        course_id = create_r.json()["id"]

        # Create a chapter (required for publish validation)
        chapter_r = client.post(
            f"/api/admin/courses/{course_id}/chapters",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Chapter 1"}
        )
        assert chapter_r.status_code in (200, 201), f"Chapter creation failed: {chapter_r.text}"
        chapter_id = chapter_r.json()["id"]

        # Create a lesson (required for publish validation)
        lesson_r = client.post(
            f"/api/admin/lessons?module_id={chapter_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Lesson 1", "lesson_type": "text", "content_text": "Hello"}
        )
        assert lesson_r.status_code in (200, 201), f"Lesson creation failed: {lesson_r.text}"

        r = client.post(
            f"/api/admin/courses/{course_id}/publish?price_tokens=0&price_dt=0",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert r.status_code == 200
        assert r.json()["status"] == "published"
        assert r.json()["is_published"] is True

    def test_unpublish_course(self, client, admin_token):
        create_r = client.post(
            "/api/admin/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Unpublish Me"}
        )
        course_id = create_r.json()["id"]
        client.post(
            f"/api/admin/courses/{course_id}/publish?price_tokens=0",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        r = client.post(
            f"/api/admin/courses/{course_id}/unpublish",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert r.status_code == 200
        assert r.json()["status"] == "draft"

    def test_duplicate_course(self, client, admin_token):
        create_r = client.post(
            "/api/admin/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Original Course", "level": "beginner"}
        )
        course_id = create_r.json()["id"]

        r = client.post(
            f"/api/admin/courses/{course_id}/duplicate",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert r.status_code == 200
        assert "Copie" in r.json()["title"]
        assert r.json()["id"] != course_id
        assert r.json()["status"] == "draft"

    def test_reorder_chapters(self, client, admin_token):
        cr = client.post(
            "/api/admin/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Reorder Test"}
        )
        course_id = cr.json()["id"]

        c1 = client.post(
            f"/api/admin/courses/{course_id}/chapters",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Chapter 1"}
        )
        c2 = client.post(
            f"/api/admin/courses/{course_id}/chapters",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Chapter 2"}
        )
        c1_id, c2_id = c1.json()["id"], c2.json()["id"]

        r = client.post(
            f"/api/admin/courses/{course_id}/reorder",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"order": [c2_id, c1_id]}
        )
        assert r.status_code == 200
        assert r.json()["success"] is True

    def test_search_courses(self, client, admin_token):
        client.post(
            "/api/admin/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Python Programming"}
        )
        client.post(
            "/api/admin/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Web Development"}
        )

        r = client.get(
            "/api/admin/courses?search=Python",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    def test_course_analytics(self, client, admin_token):
        cr = client.post(
            "/api/admin/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Analytics Course"}
        )
        course_id = cr.json()["id"]

        r = client.get(
            f"/api/admin/courses/{course_id}/analytics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert r.status_code == 200
        data = r.json()
        assert "total_enrolled" in data
        assert "total_lessons" in data
        assert "total_modules" in data


class TestAdminChapters:
    """Chapter management tests."""

    def test_create_chapter(self, client, admin_token):
        cr = client.post(
            "/api/admin/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Course for Chapters"}
        )
        course_id = cr.json()["id"]

        r = client.post(
            f"/api/admin/courses/{course_id}/chapters",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Chapter 1", "description": "Intro"}
        )
        assert r.status_code == 200
        assert r.json()["title"] == "Chapter 1"
        assert r.json()["id"] > 0

    def test_update_chapter(self, client, admin_token):
        cr = client.post(
            "/api/admin/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Course"}
        )
        course_id = cr.json()["id"]
        chap = client.post(
            f"/api/admin/courses/{course_id}/chapters",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Old Title"}
        )
        chap_id = chap.json()["id"]

        r = client.patch(
            f"/api/admin/courses/{course_id}/chapters/{chap_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "New Title", "order_index": 5}
        )
        assert r.status_code == 200
        assert r.json()["title"] == "New Title"

    def test_delete_chapter(self, client, admin_token):
        cr = client.post(
            "/api/admin/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Course"}
        )
        course_id = cr.json()["id"]
        chap = client.post(
            f"/api/admin/courses/{course_id}/chapters",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "To Delete"}
        )
        chap_id = chap.json()["id"]

        r = client.delete(
            f"/api/admin/courses/{course_id}/chapters/{chap_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert r.status_code == 204


class TestAdminLessons:
    """Lesson management tests."""

    def test_create_lesson(self, client, admin_token):
        cr = client.post(
            "/api/admin/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Course with Lessons"}
        )
        course_id = cr.json()["id"]
        chap = client.post(
            f"/api/admin/courses/{course_id}/chapters",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Chapter 1"}
        )
        chapter_id = chap.json()["id"]

        r = client.post(
            f"/api/admin/lessons?module_id={chapter_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Lesson 1", "lesson_type": "text", "content_text": "Hello world"}
        )
        assert r.status_code == 201
        assert r.json()["title"] == "Lesson 1"
        assert r.json()["chapter_id"] == chapter_id

    def test_update_lesson(self, client, admin_token):
        cr = client.post(
            "/api/admin/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Course"}
        )
        course_id = cr.json()["id"]
        chap = client.post(
            f"/api/admin/courses/{course_id}/chapters",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Chapter"}
        )
        chapter_id = chap.json()["id"]
        lesson = client.post(
            f"/api/admin/lessons?module_id={chapter_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Old Lesson"}
        )
        lesson_id = lesson.json()["id"]

        r = client.patch(
            f"/api/admin/lessons/{lesson_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Updated Lesson", "content_text": "New content"}
        )
        assert r.status_code == 200
        assert r.json()["title"] == "Updated Lesson"

    def test_delete_lesson(self, client, admin_token):
        cr = client.post(
            "/api/admin/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Course"}
        )
        course_id = cr.json()["id"]
        chap = client.post(
            f"/api/admin/courses/{course_id}/chapters",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Chapter"}
        )
        chapter_id = chap.json()["id"]
        lesson = client.post(
            f"/api/admin/lessons?module_id={chapter_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "To Delete"}
        )
        lesson_id = lesson.json()["id"]

        r = client.delete(
            f"/api/admin/lessons/{lesson_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert r.status_code == 204

    def test_reorder_lessons(self, client, admin_token):
        cr = client.post(
            "/api/admin/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Course"}
        )
        course_id = cr.json()["id"]
        chap = client.post(
            f"/api/admin/courses/{course_id}/chapters",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Chapter"}
        )
        chapter_id = chap.json()["id"]
        l1 = client.post(
            f"/api/admin/lessons?module_id={chapter_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "L1"}
        )
        l2 = client.post(
            f"/api/admin/lessons?module_id={chapter_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "L2"}
        )
        l1_id, l2_id = l1.json()["id"], l2.json()["id"]

        r = client.post(
            "/api/admin/lessons/reorder",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"order": [l2_id, l1_id]}
        )
        assert r.status_code == 200
        assert r.json()["success"] is True


class TestAdminQuizzes:
    """Quiz management tests."""

    def test_create_quiz(self, client, admin_token):
        cr = client.post(
            "/api/admin/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Course for Quiz"}
        )
        course_id = cr.json()["id"]
        chap = client.post(
            f"/api/admin/courses/{course_id}/chapters",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Chapter"}
        )
        chapter_id = chap.json()["id"]
        lesson = client.post(
            f"/api/admin/lessons?module_id={chapter_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Lesson"}
        )
        lesson_id = lesson.json()["id"]

        r = client.post(
            "/api/admin/quizzes",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"lesson_id": lesson_id, "title": "Test Quiz", "time_limit_minutes": 10}
        )
        assert r.status_code in (200, 201)
        assert r.json()["title"] == "Test Quiz"
        assert r.json()["id"] > 0

    def test_add_question_to_quiz(self, client, admin_token):
        cr = client.post("/api/admin/courses", headers={"Authorization": f"Bearer {admin_token}"}, json={"title": "C"})
        cid = cr.json()["id"]
        ch = client.post(f"/api/admin/courses/{cid}/chapters", headers={"Authorization": f"Bearer {admin_token}"}, json={"title": "Ch"})
        chid = ch.json()["id"]
        le = client.post(f"/api/admin/lessons?module_id={chid}", headers={"Authorization": f"Bearer {admin_token}"}, json={"title": "L"})
        leid = le.json()["id"]
        qz = client.post("/api/admin/quizzes", headers={"Authorization": f"Bearer {admin_token}"}, json={"lesson_id": leid, "title": "Q"})

        r = client.post(
            f"/api/admin/quizzes/{qz.json()['id']}/questions",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"text": "What is 2+2?", "question_type": "multiple_choice", "points": 1}
        )
        assert r.status_code in (200, 201)
        assert r.json()["text"] == "What is 2+2?"

    def test_add_option_to_question(self, client, admin_token):
        cr = client.post("/api/admin/courses", headers={"Authorization": f"Bearer {admin_token}"}, json={"title": "C"})
        cid = cr.json()["id"]
        ch = client.post(f"/api/admin/courses/{cid}/chapters", headers={"Authorization": f"Bearer {admin_token}"}, json={"title": "Ch"})
        chid = ch.json()["id"]
        le = client.post(f"/api/admin/lessons?module_id={chid}", headers={"Authorization": f"Bearer {admin_token}"}, json={"title": "L"})
        leid = le.json()["id"]
        qz = client.post("/api/admin/quizzes", headers={"Authorization": f"Bearer {admin_token}"}, json={"lesson_id": leid, "title": "Q"})

        r = client.post(
            f"/api/admin/quizzes/{qz.json()['id']}/questions",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"text": "What is 2+2?", "question_type": "multiple_choice", "points": 1}
        )
        assert r.status_code in (200, 201)
        assert r.json()["text"] == "What is 2+2?"

    def test_add_option_to_question(self, client, admin_token):
        cr = client.post("/api/admin/courses", headers={"Authorization": f"Bearer {admin_token}"}, json={"title": "C"})
        cid = cr.json()["id"]
        ch = client.post(f"/api/admin/courses/{cid}/chapters", headers={"Authorization": f"Bearer {admin_token}"}, json={"title": "Ch"})
        chid = ch.json()["id"]
        le = client.post(f"/api/admin/lessons?module_id={chid}", headers={"Authorization": f"Bearer {admin_token}"}, json={"title": "L"})
        leid = le.json()["id"]
        qz = client.post("/api/admin/quizzes", headers={"Authorization": f"Bearer {admin_token}"}, json={"lesson_id": leid, "title": "Q"})
        qzid = qz.json()["id"]
        q = client.post(f"/api/admin/quizzes/{qzid}/questions", headers={"Authorization": f"Bearer {admin_token}"}, json={"text": "Color?", "question_type": "multiple_choice"})
        qid = q.json()["id"]

        r = client.post(
            f"/api/admin/quizzes/{qzid}/questions/{qid}/options",
            headers={"Authorization": f"Bearer {admin_token}"},
json={"text": "Red", "is_correct": True}
        )
        assert r.status_code in (200, 201)
        assert r.json()["text"] == "Red"

    def test_update_quiz(self, client, admin_token):
        cr = client.post("/api/admin/courses", headers={"Authorization": f"Bearer {admin_token}"}, json={"title": "C"})
        cid = cr.json()["id"]
        ch = client.post(f"/api/admin/courses/{cid}/chapters", headers={"Authorization": f"Bearer {admin_token}"}, json={"title": "Ch"})
        chid = ch.json()["id"]
        le = client.post(f"/api/admin/lessons?module_id={chid}", headers={"Authorization": f"Bearer {admin_token}"}, json={"title": "L"})
        leid = le.json()["id"]
        qz = client.post("/api/admin/quizzes", headers={"Authorization": f"Bearer {admin_token}"}, json={"lesson_id": leid, "title": "Quiz"})
        qzid = qz.json()["id"]

        r = client.patch(
            f"/api/admin/quizzes/{qzid}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Updated Quiz"}
        )
        assert r.status_code == 200
        assert r.json()["title"] == "Updated Quiz"

    def test_delete_quiz(self, client, admin_token):
        cr = client.post("/api/admin/courses", headers={"Authorization": f"Bearer {admin_token}"}, json={"title": "C"})
        cid = cr.json()["id"]
        ch = client.post(f"/api/admin/courses/{cid}/chapters", headers={"Authorization": f"Bearer {admin_token}"}, json={"title": "Ch"})
        chid = ch.json()["id"]
        le = client.post(f"/api/admin/lessons?module_id={chid}", headers={"Authorization": f"Bearer {admin_token}"}, json={"title": "L"})
        leid = le.json()["id"]
        qz = client.post("/api/admin/quizzes", headers={"Authorization": f"Bearer {admin_token}"}, json={"lesson_id": leid, "title": "Q"})
        qzid = qz.json()["id"]

        r = client.delete(
            f"/api/admin/quizzes/{qzid}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert r.status_code == 204


class TestCORS:
    """CORS header tests."""

    def test_cors_headers_on_get(self, client):
        r = client.get(
            "/api/admin/courses",
            headers={"Origin": "http://localhost:5173"}
        )
        header_keys_lower = [k.lower() for k in r.headers.keys()]
        assert "access-control-allow-origin" in header_keys_lower

    def test_cors_headers_on_options(self, client):
        r = client.options(
            "/api/admin/courses",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            }
        )
        assert r.status_code in (200, 204)


class TestHealth:
    """Health check tests."""

    def test_health_endpoint(self, client):
        r = client.get("/health")
        assert r.status_code in (200, 503)
        assert "status" in r.json()

    def test_root_endpoint(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "name" in r.json()