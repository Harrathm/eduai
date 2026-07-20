"""
Migration: Add missing school_id columns and ForeignKey constraints.
This migration is designed to be safe and idempotent.
"""

from sqlalchemy import text
from app.db import engine


def migrate():
    with engine.connect() as conn:
        # Add school_id to models that need it for multi-tenant isolation
        migrations = [
            # CourseEnrollment - add school_id
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='course_enrollments' AND column_name='school_id') THEN
                    ALTER TABLE course_enrollments ADD COLUMN school_id INTEGER;
                    CREATE INDEX IF NOT EXISTS ix_course_enrollments_school_id ON course_enrollments(school_id);
                END IF;
            END $$;
            """,
            
            # ClassroomEnrollment - add school_id
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='classroom_enrollments' AND column_name='school_id') THEN
                    ALTER TABLE classroom_enrollments ADD COLUMN school_id INTEGER;
                    CREATE INDEX IF NOT EXISTS ix_classroom_enrollments_school_id ON classroom_enrollments(school_id);
                END IF;
            END $$;
            """,
            
            # CoursePurchase - add school_id
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='course_purchases' AND column_name='school_id') THEN
                    ALTER TABLE course_purchases ADD COLUMN school_id INTEGER;
                    CREATE INDEX IF NOT EXISTS ix_course_purchases_school_id ON course_purchases(school_id);
                END IF;
            END $$;
            """,
            
            # AuditLog - add school_id (critical for compliance)
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='audit_logs' AND column_name='school_id') THEN
                    ALTER TABLE audit_logs ADD COLUMN school_id INTEGER;
                    CREATE INDEX IF NOT EXISTS ix_audit_logs_school_id ON audit_logs(school_id);
                END IF;
            END $$;
            """,
            
            # Payment - add school_id
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='payments' AND column_name='school_id') THEN
                    ALTER TABLE payments ADD COLUMN school_id INTEGER;
                    CREATE INDEX IF NOT EXISTS ix_payments_school_id ON payments(school_id);
                END IF;
            END $$;
            """,
            
            # WalletTransaction - add school_id
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='wallet_transactions' AND column_name='school_id') THEN
                    ALTER TABLE wallet_transactions ADD COLUMN school_id INTEGER;
                    CREATE INDEX IF NOT EXISTS ix_wallet_transactions_school_id ON wallet_transactions(school_id);
                END IF;
            END $$;
            """,
            
            # MediaAsset - add school_id
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='media_assets' AND column_name='school_id') THEN
                    ALTER TABLE media_assets ADD COLUMN school_id INTEGER;
                    CREATE INDEX IF NOT EXISTS ix_media_assets_school_id ON media_assets(school_id);
                END IF;
            END $$;
            """,
            
            # Add missing ForeignKeys
            # Note.user_id -> users.id
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name='fk_notes_user_id') THEN
                    ALTER TABLE notes ADD CONSTRAINT fk_notes_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
                END IF;
            END $$;
            """,
            
            # Note.lesson_id -> lessons.id
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name='fk_notes_lesson_id') THEN
                    ALTER TABLE notes ADD CONSTRAINT fk_notes_lesson_id FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE;
                END IF;
            END $$;
            """,
            
            # Bookmark.user_id -> users.id
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name='fk_bookmarks_user_id') THEN
                    ALTER TABLE bookmarks ADD CONSTRAINT fk_bookmarks_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
                END IF;
            END $$;
            """,
            
            # Bookmark.lesson_id -> lessons.id
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name='fk_bookmarks_lesson_id') THEN
                    ALTER TABLE bookmarks ADD CONSTRAINT fk_bookmarks_lesson_id FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE;
                END IF;
            END $$;
            """,
            
            # LessonProgress.enrollment_id -> course_enrollments.id
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name='fk_lesson_progress_enrollment_id') THEN
                    ALTER TABLE lesson_progress ADD CONSTRAINT fk_lesson_progress_enrollment_id FOREIGN KEY (enrollment_id) REFERENCES course_enrollments(id) ON DELETE CASCADE;
                END IF;
            END $$;
            """,
            
            # LessonProgress.lesson_id -> lessons.id
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name='fk_lesson_progress_lesson_id') THEN
                    ALTER TABLE lesson_progress ADD CONSTRAINT fk_lesson_progress_lesson_id FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE;
                END IF;
            END $$;
            """,
            
            # Certificate.student_id -> users.id
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name='fk_certificates_student_id') THEN
                    ALTER TABLE certificates ADD CONSTRAINT fk_certificates_student_id FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE;
                END IF;
            END $$;
            """,
            
            # Certificate.course_id -> courses.id
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name='fk_certificates_course_id') THEN
                    ALTER TABLE certificates ADD CONSTRAINT fk_certificates_course_id FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE;
                END IF;
            END $$;
            """,
            
            # Certificate.enrollment_id -> course_enrollments.id
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name='fk_certificates_enrollment_id') THEN
                    ALTER TABLE certificates ADD CONSTRAINT fk_certificates_enrollment_id FOREIGN KEY (enrollment_id) REFERENCES course_enrollments(id) ON DELETE CASCADE;
                END IF;
            END $$;
            """,
            
            # MediaAsset.owner_id -> users.id
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name='fk_media_assets_owner_id') THEN
                    ALTER TABLE media_assets ADD CONSTRAINT fk_media_assets_owner_id FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE;
                END IF;
            END $$;
            """,
            
            # AIUsageLog.school_id -> schools.id (fix existing broken FK)
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name='fk_ai_usage_logs_school_id') THEN
                    ALTER TABLE ai_usage_logs ADD CONSTRAINT fk_ai_usage_logs_school_id FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE SET NULL;
                END IF;
            END $$;
            """,
            
            # QuizAttempt.student_id -> users.id
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name='fk_quiz_attempts_student_id') THEN
                    ALTER TABLE quiz_attempts ADD CONSTRAINT fk_quiz_attempts_student_id FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE;
                END IF;
            END $$;
            """,
            
            # QuizAnswer.question_id -> quiz_questions.id
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name='fk_quiz_answers_question_id') THEN
                    ALTER TABLE quiz_answers ADD CONSTRAINT fk_quiz_answers_question_id FOREIGN KEY (question_id) REFERENCES quiz_questions(id) ON DELETE CASCADE;
                END IF;
            END $$;
            """,
        ]
        
        for migration in migrations:
            try:
                conn.execute(text(migration))
                conn.commit()
            except Exception as e:
                print(f"Warning: {e}")
                conn.rollback()
        
        print("Migration completed: Added school_id columns and ForeignKey constraints")


if __name__ == "__main__":
    migrate()
