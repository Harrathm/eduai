"""
B2B Academy Distribution Seed Script.
Inserts test data for the School-to-Course access flow.

Run: cd backend && python seed_b2b.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.models import Base, School, User, UserRole, Course, CourseStatus, Module, Lesson, Quiz, QuizQuestion, QuizOption, SchoolCourseAccess

settings = get_settings()

engine = create_engine(settings.database_url)


def utcnow():
    return datetime.now(timezone.utc)


def main():
    print("=== B2B Academy Distribution Seed ===")
    Base.metadata.create_all(bind=engine)
    db = Session(bind=engine)

    try:
        # Clean existing B2B data if re-running
        db.execute(text("DELETE FROM school_course_access"))
        db.execute(text("DELETE FROM quiz_options WHERE question_id IN (SELECT id FROM quiz_questions WHERE quiz_id IN (SELECT id FROM quizzes WHERE lesson_id IN (SELECT id FROM lessons WHERE module_id IN (SELECT id FROM modules WHERE course_id IN (SELECT id FROM courses WHERE title LIKE 'Course %')))))"))
        db.execute(text("DELETE FROM quiz_questions WHERE quiz_id IN (SELECT id FROM quizzes WHERE lesson_id IN (SELECT id FROM lessons WHERE module_id IN (SELECT id FROM modules WHERE course_id IN (SELECT id FROM courses WHERE title LIKE 'Course %')))))"))
        db.execute(text("DELETE FROM quizzes WHERE lesson_id IN (SELECT id FROM lessons WHERE module_id IN (SELECT id FROM modules WHERE course_id IN (SELECT id FROM courses WHERE title LIKE 'Course %'))))"))
        db.execute(text("DELETE FROM lessons WHERE module_id IN (SELECT id FROM modules WHERE course_id IN (SELECT id FROM courses WHERE title LIKE 'Course %')))"))
        db.execute(text("DELETE FROM modules WHERE course_id IN (SELECT id FROM courses WHERE title LIKE 'Course %'))"))
        db.execute(text("DELETE FROM courses WHERE title LIKE 'Course %'"))
        db.execute(text("DELETE FROM users WHERE email LIKE '%b2b_test%'"))
        db.execute(text("DELETE FROM schools WHERE slug LIKE 'b2b_%'"))
        db.commit()
        print("Cleaned previous B2B test data.")
    except Exception as e:
        db.rollback()
        print(f"Clean skipped (first run?): {e}")

    # ─── 1. GET SUPER ADMIN ────────────────────────────────────────
    super_admin = db.query(User).filter(User.email == "admin@eduai.platform").first()
    if not super_admin:
        super_admin = User(
            school_id=1, email="admin@eduai.platform",
            full_name="Super Admin", role=UserRole.SUPER_ADMIN,
            hashed_password=get_password_hash("admin123"),
            is_active=True, is_approved=True,
        )
        db.add(super_admin)
        db.flush()
        print("Created super admin.")

    # ─── 2. ACADEMY COURSES (global, owned by school_id=1) ────────
    school_1 = db.query(School).filter(School.id == 1).first()
    if not school_1:
        school_1 = School(name="EDUAI Academy", slug="academy", is_active=True)
        db.add(school_1)
        db.flush()

    course_a = Course(
        school_id=school_1.id, author_id=super_admin.id,
        title="Course A: Web Development Fundamentals",
        short_description="Master HTML, CSS, and JavaScript from scratch.",
        description="""A comprehensive introduction to modern web development. 
Students will learn to build responsive websites using HTML5, CSS3, and JavaScript ES6+.
Covers DOM manipulation, async programming, and API integration.""",
        slug="course-a-web-dev",
        category="Web Development", level="beginner",
        language="fr", status=CourseStatus.PUBLISHED, is_published=True,
        price_tokens=500, price_dt=49.99,
        total_modules=3, total_lessons=7, total_duration_minutes=180,
        visibility="public", enrollment_type="open",
        tags=["html", "css", "javascript", "web"],
        published_at=utcnow(), created_at=utcnow(), updated_at=utcnow(),
    )
    db.add(course_a)
    db.flush()

    course_b = Course(
        school_id=school_1.id, author_id=super_admin.id,
        title="Course B: Python Data Science",
        short_description="Analyze data with Python, Pandas, and Matplotlib.",
        description="""A hands-on introduction to data science using Python.
Covers NumPy arrays, Pandas DataFrames, data visualization with Matplotlib,
and basic machine learning with Scikit-learn. Includes real-world datasets.""",
        slug="course-b-python-data-science",
        category="Data Science", level="intermediate",
        language="fr", status=CourseStatus.PUBLISHED, is_published=True,
        price_tokens=800, price_dt=79.99,
        total_modules=3, total_lessons=8, total_duration_minutes=240,
        visibility="public", enrollment_type="open",
        tags=["python", "data-science", "pandas", "numpy"],
        published_at=utcnow(), created_at=utcnow(), updated_at=utcnow(),
    )
    db.add(course_b)
    db.flush()

    # ─── Modules & Lessons for Course A ────────────────────────────
    mod_a1 = Module(course_id=course_a.id, title="HTML Foundations", description="Learn HTML5 semantics and structure.", order=1)
    db.add(mod_a1); db.flush()
    lessons_a1 = [
        Lesson(module_id=mod_a1.id, title="HTML Document Structure", content_text="An HTML document begins with <!DOCTYPE html>...\n\nSemantic elements like <header>, <nav>, <main>, and <footer> provide structure. Accessibility attributes like 'role' and 'aria-label' improve screen reader support.", lesson_type="TEXT", order=1, duration_minutes=25, is_free=True),
        Lesson(module_id=mod_a1.id, title="Forms & Input Validation", content_text="HTML forms collect user data. Use <input> with type='email', 'number', 'tel' for native validation. The 'required' attribute prevents empty submissions. Pattern attribute allows regex validation.", lesson_type="TEXT", order=2, duration_minutes=30),
        Lesson(module_id=mod_a1.id, title="Multimedia Elements", content_text="Embed images with <img>, videos with <video>, and audio with <audio>. The 'loading=lazy' attribute defers offscreen image loading. Use <figure> and <figcaption> for annotated media.", lesson_type="TEXT", order=3, duration_minutes=20),
    ]
    for l in lessons_a1: db.add(l)
    db.flush()

    mod_a2 = Module(course_id=course_a.id, title="CSS Styling", description="Modern CSS layouts and responsive design.", order=2)
    db.add(mod_a2); db.flush()
    lessons_a2 = [
        Lesson(module_id=mod_a2.id, title="Flexbox & Grid Layouts", content_text="Flexbox: display:flex, justify-content, align-items, flex-wrap. Grid: display:grid, grid-template-columns, gap. Use 'auto-fit' and 'minmax()' for responsive grids without media queries.", lesson_type="TEXT", order=1, duration_minutes=35),
        Lesson(module_id=mod_a2.id, title="CSS Custom Properties & Animations", content_text="Custom properties (--primary-color) enable theme switching. CSS animations use @keyframes. Transitions with 'transition: property duration timing-function' create smooth UI interactions.", lesson_type="TEXT", order=2, duration_minutes=25),
    ]
    for l in lessons_a2: db.add(l)
    db.flush()

    mod_a3 = Module(course_id=course_a.id, title="JavaScript Basics", description="Programming fundamentals with JavaScript.", order=3)
    db.add(mod_a3); db.flush()
    lessons_a3 = [
        Lesson(module_id=mod_a3.id, title="Variables, Functions & DOM", content_text="'let', 'const', and arrow functions. document.querySelector() and addEventListener(). Event delegation improves performance. Use 'data-*' attributes to store DOM metadata.", lesson_type="TEXT", order=1, duration_minutes=30),
        Lesson(module_id=mod_a3.id, title="Async JavaScript & Fetch API", content_text="Promises: .then() and .catch(). async/await syntax. Fetch API for HTTP requests. Handle errors with try/catch. Use AbortController for request cancellation.", lesson_type="TEXT", order=2, duration_minutes=35),
    ]
    for l in lessons_a3: db.add(l)
    db.flush()

    # ─── Modules & Lessons for Course B ────────────────────────────
    mod_b1 = Module(course_id=course_b.id, title="Python & NumPy", description="Scientific computing with NumPy arrays.", order=1)
    db.add(mod_b1); db.flush()
    lessons_b1 = [
        Lesson(module_id=mod_b1.id, title="NumPy Array Operations", content_text="Create arrays with np.array(), np.zeros(), np.ones(). Vectorized operations eliminate Python loops. Broadcasting enables arithmetic on differently-shaped arrays.", lesson_type="TEXT", order=1, duration_minutes=30),
        Lesson(module_id=mod_b1.id, title="Linear Algebra with NumPy", content_text="Matrix multiplication with np.dot() and @ operator. Eigenvalues with np.linalg.eig(). Solving linear systems with np.linalg.solve().", lesson_type="TEXT", order=2, duration_minutes=35),
    ]
    for l in lessons_b1: db.add(l)
    db.flush()

    mod_b2 = Module(course_id=course_b.id, title="Pandas Data Analysis", description="Data manipulation with Pandas DataFrames.", order=2)
    db.add(mod_b2); db.flush()
    lessons_b2 = [
        Lesson(module_id=mod_b2.id, title="DataFrame Fundamentals", content_text="Create DataFrames from dicts, CSV, or SQL. Use .head(), .info(), .describe() for exploration. Filter with boolean indexing. Handle missing data with .dropna() and .fillna().", lesson_type="TEXT", order=1, duration_minutes=30),
        Lesson(module_id=mod_b2.id, title="GroupBy & Aggregations", content_text="Split-apply-combine with .groupby(). Aggregate with .sum(), .mean(), .agg(). Pivot tables with .pivot_table(). Merge DataFrames with pd.merge() using inner/outer/left/right joins.", lesson_type="TEXT", order=2, duration_minutes=35),
        Lesson(module_id=mod_b2.id, title="Time Series Analysis", content_text="Parse dates with pd.to_datetime(). Set DatetimeIndex for resampling. Rolling windows with .rolling(). Shift for lag features. Diff and pct_change for returns.", lesson_type="TEXT", order=3, duration_minutes=25),
    ]
    for l in lessons_b2: db.add(l)
    db.flush()

    mod_b3 = Module(course_id=course_b.id, title="Data Visualization", description="Plotting with Matplotlib and Seaborn.", order=3)
    db.add(mod_b3); db.flush()
    lessons_b3 = [
        Lesson(module_id=mod_b3.id, title="Matplotlib Custom Plots", content_text="Figure and Axes objects. Line plots, scatter plots, bar charts. Customize with labels, titles, legends, and colormaps. Subplots with plt.subplots(). Save figures with .savefig().", lesson_type="TEXT", order=1, duration_minutes=30),
        Lesson(module_id=mod_b3.id, title="Statistical Plots with Seaborn", content_text="Distribution plots: histplot, kdeplot, boxplot. Relational plots: scatterplot, lineplot. Categorical plots: barplot, countplot. Heatmaps for correlation matrices.", lesson_type="TEXT", order=2, duration_minutes=25),
    ]
    for l in lessons_b3: db.add(l)
    db.flush()

    # ─── QUIZZES for Course A ──────────────────────────────────────
    quiz_a1_lesson = lessons_a1[0]
    quiz_a1 = Quiz(lesson_id=quiz_a1_lesson.id, title="HTML Structure Quiz", passing_score_percent=70, max_attempts=3, total_points=20)
    db.add(quiz_a1); db.flush()
    quiz_a1_lesson.quiz_id = quiz_a1.id
    qa1_1 = QuizQuestion(quiz_id=quiz_a1.id, question_text="Which HTML element is used to define navigation links?", question_type="mcq", points=10, order_index=1)
    db.add(qa1_1); db.flush()
    for opt in [
        QuizOption(question_id=qa1_1.id, option_text="<nav>", is_correct=True, order_index=1),
        QuizOption(question_id=qa1_1.id, option_text="<navigate>", is_correct=False, order_index=2),
        QuizOption(question_id=qa1_1.id, option_text="<menu>", is_correct=False, order_index=3),
        QuizOption(question_id=qa1_1.id, option_text="<header>", is_correct=False, order_index=4),
    ]: db.add(opt)
    qa1_2 = QuizQuestion(quiz_id=quiz_a1.id, question_text="What does the 'aria-label' attribute do?", question_type="mcq", points=10, order_index=2)
    db.add(qa1_2); db.flush()
    for opt in [
        QuizOption(question_id=qa1_2.id, option_text="Provides an accessible label for screen readers", is_correct=True, order_index=1),
        QuizOption(question_id=qa1_2.id, option_text="Adds a tooltip on hover", is_correct=False, order_index=2),
        QuizOption(question_id=qa1_2.id, option_text="Defines a hyperlink target", is_correct=False, order_index=3),
        QuizOption(question_id=qa1_2.id, option_text="Sets the character encoding", is_correct=False, order_index=4),
    ]: db.add(opt)

    # ─── QUIZZES for Course B ──────────────────────────────────────
    quiz_b1_lesson = lessons_b1[0]
    quiz_b1 = Quiz(lesson_id=quiz_b1_lesson.id, title="NumPy Basics Quiz", passing_score_percent=70, max_attempts=3, total_points=20)
    db.add(quiz_b1); db.flush()
    quiz_b1_lesson.quiz_id = quiz_b1.id
    qb1_1 = QuizQuestion(quiz_id=quiz_b1.id, question_text="Which NumPy function creates an array of zeros?", question_type="mcq", points=10, order_index=1)
    db.add(qb1_1); db.flush()
    for opt in [
        QuizOption(question_id=qb1_1.id, option_text="np.zeros()", is_correct=True, order_index=1),
        QuizOption(question_id=qb1_1.id, option_text="np.empty()", is_correct=False, order_index=2),
        QuizOption(question_id=qb1_1.id, option_text="np.ones()", is_correct=False, order_index=3),
        QuizOption(question_id=qb1_1.id, option_text="np.array()", is_correct=False, order_index=4),
    ]: db.add(opt)
    qb1_2 = QuizQuestion(quiz_id=quiz_b1.id, question_text="What is broadcasting in NumPy?", question_type="mcq", points=10, order_index=2)
    db.add(qb1_2); db.flush()
    for opt in [
        QuizOption(question_id=qb1_2.id, option_text="Performing operations on arrays of different shapes", is_correct=True, order_index=1),
        QuizOption(question_id=qb1_2.id, option_text="Sending data over a network", is_correct=False, order_index=2),
        QuizOption(question_id=qb1_2.id, option_text="Logging array values to console", is_correct=False, order_index=3),
        QuizOption(question_id=qb1_2.id, option_text="Converting arrays to Python lists", is_correct=False, order_index=4),
    ]: db.add(opt)

    db.flush()

    # ─── 3. TEST SCHOOLS ──────────────────────────────────────────
    school_eit = School(
        name="École Internationale de Tunis",
        slug="b2b_ecole_internationale_tunis",
        domain="eit.tn",
        subscription_tier="premium",
        max_users=100, is_active=True,
        created_at=utcnow(), updated_at=utcnow(),
    )
    db.add(school_eit); db.flush()

    school_lp = School(
        name="Lycée Pilote",
        slug="b2b_lycee_pilote",
        domain="lycee-pilote.tn",
        subscription_tier="enterprise",
        max_users=500, is_active=True,
        created_at=utcnow(), updated_at=utcnow(),
    )
    db.add(school_lp); db.flush()

    # ─── 4. SCHOOL ADMINS ──────────────────────────────────────────
    admin_eit = User(
        school_id=school_eit.id, email="admin.eit@b2b_test.edu",
        full_name="Amel Ben Ali", role=UserRole.ADMIN_SCHOOL,
        hashed_password=get_password_hash("admin123"),
        is_active=True, is_approved=True,
        created_at=utcnow(),
    )
    db.add(admin_eit); db.flush()

    admin_lp = User(
        school_id=school_lp.id, email="admin.lp@b2b_test.edu",
        full_name="Mehdi Trabelsi", role=UserRole.ADMIN_SCHOOL,
        hashed_password=get_password_hash("admin123"),
        is_active=True, is_approved=True,
        created_at=utcnow(),
    )
    db.add(admin_lp); db.flush()

    # ─── 5. ATTRIBUTION (SchoolCourseAccess) ─────────────────────
    # École Internationale de Tunis -> Course A only
    sca_eit_a = SchoolCourseAccess(
        school_id=school_eit.id, course_id=course_a.id,
        purchased_at=utcnow(), is_active=True,
        granted_by=super_admin.id, price_paid_dt=49.99,
    )
    db.add(sca_eit_a)

    # Lycée Pilote -> Course A AND Course B
    sca_lp_a = SchoolCourseAccess(
        school_id=school_lp.id, course_id=course_a.id,
        purchased_at=utcnow(), is_active=True,
        granted_by=super_admin.id, price_paid_dt=49.99,
    )
    db.add(sca_lp_a)
    sca_lp_b = SchoolCourseAccess(
        school_id=school_lp.id, course_id=course_b.id,
        purchased_at=utcnow(), is_active=True,
        granted_by=super_admin.id, price_paid_dt=79.99,
    )
    db.add(sca_lp_b)

    # ─── 6. END USERS (students + teachers per school) ─────────────
    users_eit = [
        User(school_id=school_eit.id, email="student1.eit@b2b_test.edu",
             full_name="Sami Khelil", role=UserRole.STUDENT,
             hashed_password=get_password_hash("pass123"), is_active=True,
             token_balance=200, dt_balance=15.0, created_at=utcnow()),
        User(school_id=school_eit.id, email="student2.eit@b2b_test.edu",
             full_name="Nour Jebali", role=UserRole.STUDENT,
             hashed_password=get_password_hash("pass123"), is_active=True,
             token_balance=350, dt_balance=25.0, created_at=utcnow()),
        User(school_id=school_eit.id, email="teacher.eit@b2b_test.edu",
             full_name="Haythem Bouazizi", role=UserRole.TEACHER,
             hashed_password=get_password_hash("pass123"), is_active=True,
             is_approved=True, token_balance=1000, dt_balance=50.0,
             created_at=utcnow()),
    ]
    for u in users_eit: db.add(u)

    users_lp = [
        User(school_id=school_lp.id, email="student1.lp@b2b_test.edu",
             full_name="Ines Gharbi", role=UserRole.STUDENT,
             hashed_password=get_password_hash("pass123"), is_active=True,
             token_balance=500, dt_balance=30.0, created_at=utcnow()),
        User(school_id=school_lp.id, email="student2.lp@b2b_test.edu",
             full_name="Omar Mami", role=UserRole.STUDENT,
             hashed_password=get_password_hash("pass123"), is_active=True,
             token_balance=180, dt_balance=10.0, created_at=utcnow()),
        User(school_id=school_lp.id, email="teacher.lp@b2b_test.edu",
             full_name="Salma Kacem", role=UserRole.TEACHER,
             hashed_password=get_password_hash("pass123"), is_active=True,
             is_approved=True, token_balance=2000, dt_balance=100.0,
             created_at=utcnow()),
    ]
    for u in users_lp: db.add(u)

    db.commit()

    # ─── 7. VERIFICATION QUERY ────────────────────────────────────
    print("\n=== VERIFICATION ===")
    for school in [school_eit, school_lp]:
        accesses = db.query(SchoolCourseAccess).filter(
            SchoolCourseAccess.school_id == school.id,
            SchoolCourseAccess.is_active == True,
        ).all()
        course_ids = [a.course_id for a in accesses]
        courses = db.query(Course).filter(Course.id.in_(course_ids)).all()
        enrolled_users = db.query(User).filter(
            User.school_id == school.id,
            User.role.in_([UserRole.STUDENT, UserRole.TEACHER]),
        ).count()
        print(f"\n{school.name} ({school.slug}):")
        print(f"  School Admin: {admin_eit.email if school.id == school_eit.id else admin_lp.email}")
        print(f"  End Users: {enrolled_users}")
        for c in courses:
            student_count = db.query(User).filter(
                User.school_id == school.id, User.role == UserRole.STUDENT
            ).count()
            print(f"  ✓ Access to: \"{c.title}\" (purchased, ${c.price_dt})")
            print(f"    → {student_count} students can access this course")

    # ─── EXAMPLE: Student sees only courses their school purchased ─
    print("\n=== STUDENT VIEW (SQLAlchemy ORM) ===")
    student = users_eit[0]  # student1.eit
    accessible = db.query(Course).join(SchoolCourseAccess).filter(
        SchoolCourseAccess.school_id == student.school_id,
        SchoolCourseAccess.is_active == True,
        Course.is_published == True,
    ).all()
    print(f"Student '{student.full_name}' (school_id={student.school_id}) sees {len(accessible)} course(s):")
    for c in accessible:
        print(f"  - {c.title}")

    db.close()
    print("\n✅ B2B seed complete!")


if __name__ == "__main__":
    main()
