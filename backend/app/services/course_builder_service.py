"""
lms.Course Builder Service - Core business logic for publishing, validation, versioning
"""

from datetime import datetime, timezone
from typing import Optional
import secrets

from sqlalchemy.orm import Session

from app.models_lms import CourseContent, Chapter, Lesson, CourseEnrollment, LessonProgress, Certificate


class CourseBuilderService:
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_slug(self, title: str) -> str:
        base_slug = title.lower().replace(" ", "-")
        base_slug = "".join(c for c in base_slug if c.isalnum() or c == "-")[:100]
        
        slug = base_slug
        counter = 1
        while self.db.query(CourseContent).filter(CourseContent.slug == slug).first():
            slug = f"{base_slug[:95]}-{counter}"
            counter += 1
        return slug
    
    def validate_for_publish(self, course_id: int) -> dict:
        """Validate course can be published"""
        course = self.db.query(CourseContent).filter(CourseContent.id == course_id).first()
        if not course:
            return {"valid": False, "errors": ["Course not found"]}
        
        errors = []
        warnings = []
        
        if not course.chapters or len(course.chapters) == 0:
            errors.append("Course must have at least 1 chapter")
        
        # Check each chapter has lessons
        for ch in course.chapters or []:
            if not ch.lessons or len(ch.lessons) == 0:
                errors.append(f"Chapter '{ch.title}' has no lessons")
        
        # Check cover
        if not course.cover_url:
            warnings.append("No cover image set")
        
        # Check description length
        if not course.description or len(course.description or "") < 100:
            errors.append("Description must be at least 100 characters")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def publish(self, course_id: int, author_id: int, price_tokens: int = 0, price_dt: float = 0.0) -> lms.Course:
        """Publish a course"""
        course = self.db.query(lms.Course).filter(lms.Course.id == course_id).first()
        if not course:
            raise ValueError("lms.Course not found")
        
        # Validate
        validation = self.validate_for_publish(course_id)
        if not validation["valid"]:
            raise ValueError(f"Cannot publish: {', '.join(validation['errors'])}")
        
        # Update
        course.status = "published"
        course.published_at = datetime.now(timezone.utc)
        course.version += 1
        course.price_tokens = price_tokens
        course.price_dt = price_dt
        course.is_free = price_tokens == 0 and price_dt == 0
        
        self.db.commit()
        self.db.refresh(course)
        
        return course
    
    def unpublish(self, course_id: int) -> lms.Course:
        """Unpublish a course"""
        course = self.db.query(lms.Course).filter(lms.Course.id == course_id).first()
        if not course:
            raise ValueError("lms.Course not found")
        
        course.status = "draft"
        course.published_at = None
        
        self.db.commit()
        self.db.refresh(course)
        
        return course
    
    def duplicate(self, course_id: int, author_id: int) -> CourseContent:
        """Create a copy of a course"""
        original = self.db.query(CourseContent).filter(CourseContent.id == course_id).first()
        if not original:
            raise ValueError("Course not found")
        
        new_course = CourseContent(
            school_id=original.school_id,
            author_id=author_id,
            title=f"{original.title} (Copy)",
            slug=self.generate_slug(original.title),
            description=original.description,
            cover_url=original.cover_url,
            meta_title=original.meta_title,
            meta_description=original.meta_description,
            price_tokens=original.price_tokens,
            price_dt=original.price_dt,
            is_free=original.is_free,
            category=original.category,
            level=original.level,
            language=original.language,
            tags=original.tags,
            estimated_duration_minutes=original.estimated_duration_minutes,
            status="draft"
        )
        self.db.add(new_course)
        self.db.flush()
        
        # Duplicate chapters and lessons (simplified - full implementation would recursively copy)
        for ch in original.chapters or []:
            new_ch = Chapter(
                course_id=new_course.id,
                title=ch.title,
                description=ch.description,
                cover_url=ch.cover_url,
                order_index=ch.order_index
            )
            self.db.add(new_ch)
            self.db.flush()
            
            for lesson in ch.lessons or []:
                new_lesson = Lesson(
                    chapter_id=new_ch.id,
                    title=lesson.title,
                    description=lesson.description,
                    lesson_type=lesson.lesson_type,
                    content_html=lesson.content_html,
                    content_text=lesson.content_text,
                    video_url=lesson.video_url,
                    video_duration_seconds=lesson.video_duration_seconds,
                    document_url=lesson.document_url,
                    order_index=lesson.order_index,
                    duration_minutes=lesson.duration_minutes,
                    is_free=lesson.is_free,
                    is_preview=lesson.is_preview
                )
                self.db.add(new_lesson)
        
        self.db.commit()
        self.db.refresh(new_course)
        
        return new_course


class ProgressService:
    """Track learner progress"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def update_lesson_progress(
        self, 
        enrollment_id: int, 
        lesson_id: int, 
        video_position_seconds: int = None,
        video_completed: bool = None,
        content_completed: bool = None,
        quiz_completed: bool = None,
        quiz_passed: bool = None,
        quiz_score: float = None
    ) -> dict:
        """Update progress for a single lesson"""
        progress = self.db.query(LessonProgress).filter(
            LessonProgress.enrollment_id == enrollment_id,
            LessonProgress.lesson_id == lesson_id
        ).first()
        
        if not progress:
            progress = LessonProgress(
                enrollment_id=enrollment_id,
                lesson_id=lesson_id,
                status="in_progress",
                started_at=datetime.now(timezone.utc)
            )
            self.db.add(progress)
        
        # Update fields
        if video_position_seconds is not None:
            progress.video_position_seconds = video_position_seconds
        if video_completed is not None:
            progress.video_completed = video_completed
        if content_completed is not None:
            progress.content_completed = content_completed
        if quiz_completed is not None:
            progress.quiz_completed = quiz_completed
        if quiz_passed is not None:
            progress.quiz_passed = quiz_passed
        if quiz_score is not None:
            progress.quiz_score = quiz_score
        
        # Mark complete
        if video_completed or content_completed or quiz_completed:
            progress.status = "completed"
            progress.completed_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        # Recalculate enrollment progress
        return self.recalculate_enrollment_progress(enrollment_id)
    
    def recalculate_enrollment_progress(self, enrollment_id: int) -> dict:
        """Recalculate overall course progress"""
        enrollment = self.db.query(lms.CourseEnrollment).filter(lms.CourseEnrollment.id == enrollment_id).first()
        if not enrollment:
            return {"progress_percent": 0}
        
        # Count total lessons
        total_lessons = self.db.query(Lesson).join(Chapter).filter(
            Chapter.course_id == enrollment.course_id
        ).count()
        
        if total_lessons == 0:
            return {"progress_percent": 0}
        
        # Count completed lessons
        completed = self.db.query(LessonProgress).filter(
            LessonProgress.enrollment_id == enrollment_id,
            LessonProgress.status == "completed"
        ).count()
        
        progress_percent = int((completed / total_lessons) * 100)
        enrollment.progress_percent = progress_percent
        
        # Complete enrollment if 100%
        if progress_percent >= 100:
            enrollment.status = "completed"
            enrollment.completed_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        return {
            "progress_percent": progress_percent,
            "completed_lessons": completed,
            "total_lessons": total_lessons
        }
    
    def get_enrollment(self, student_id: int, course_id: int) -> Optional[lms.CourseEnrollment]:
        """Get or create enrollment"""
        enrollment = self.db.query(lms.CourseEnrollment).filter(
            lms.CourseEnrollment.student_id == student_id,
            lms.CourseEnrollment.course_id == course_id
        ).first()
        
        if not enrollment:
            enrollment = lms.CourseEnrollment(
                student_id=student_id,
                course_id=course_id,
                status="active"
            )
            self.db.add(enrollment)
            self.db.commit()
            self.db.refresh(enrollment)
        
        return enrollment


class CertificateService:
    """Generate certificates"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_certificate(self, enrollment_id: int) -> Certificate:
        """Generate certificate if eligible"""
        enrollment = self.db.query(lms.CourseEnrollment).filter(
            lms.CourseEnrollment.id == enrollment_id
        ).first()
        
        if not enrollment or enrollment.progress_percent < 100:
            raise ValueError("Not eligible for certificate")
        
        # Check if certificate already exists
        existing = self.db.query(Certificate).filter(
            Certificate.student_id == enrollment.student_id,
            Certificate.course_id == enrollment.course_id
        ).first()
        
        if existing:
            return existing
        
        # Get course and user
        course = self.db.query(CourseContent).filter(CourseContent.id == enrollment.course_id).first()
        
        # Generate certificate
        cert = Certificate(
            student_id=enrollment.student_id,
            course_id=enrollment.course_id,
            enrollment_id=enrollment_id,
            certificate_number=f"CERT-{secrets.randbelow(1000000):06d}",
            student_name="",  # Would get from user profile
            course_name=course.title,
            verification_code=secrets.token_hex(16),
            completion_percent=enrollment.progress_percent
        )
        
        self.db.add(cert)
        self.db.commit()
        
        return cert
