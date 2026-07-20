"""Database query optimization utilities."""

from typing import List, Optional, Any, TypeVar, Type
from sqlalchemy.orm import Session, Query, joinedload, selectinload, RelationshipProperty
from sqlalchemy import func

from app.core.config import get_settings

T = TypeVar("T")


class QueryOptimizer:
    """Optimize database queries with eager loading."""
    
    # Common relationship paths for eager loading
    EAGER_LOADS = {
        "User": ["enrollments", "submissions"],
        "Course": ["modules", "purchases"],
        "Module": ["lessons"],
        "ClassRoom": ["assignments", "enrollments"],
        "Assignment": ["submissions"],
        "Lesson": ["quizzes", "media"],
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def with_eager(
        self,
        query: Query,
        model: Type,
        *relationships: str,
    ) -> Query:
        """Add eager loading to query.
        
        Args:
            query: Base query
            model: Model class
            *relationships: Relationship names to eager load
        
        Example:
            query = QueryOptimizer(db).with_eager(
                db.query(User), User, "enrollments", "submissions"
            )
        """
        for rel in relationships:
            query = query.options(joinedload(getattr(model, rel)))
        return query
    
    def with_count(self, query: Query) -> tuple[List, int]:
        """Get results with total count efficiently.
        
        If query has limit/offset, returns all results with separate count.
        Otherwise uses single query with window function.
        """
        # Check if query has limit
        if query._limit is not None or query._offset is not None:
            # Separate count query
            count_query = query.order_by(None).offset(None).limit(None)
            total = count_query.with_entities(func.count()).scalar()
            return query.all(), total
        
        # Add count to query
        query = query.add_columns(func.count().over().label("total"))
        result = query.first()
        return [result[0]] if result else [], result[1] if result else 0
    
    def paginate(
        self,
        query: Query,
        page: int = 1,
        per_page: int = 20,
    ) -> dict:
        """Paginate query efficiently.
        
        Args:
            query: Base query
            page: Page number (1-indexed)
            per_page: Items per page
        
        Returns:
            dict with items, total, page, per_page
        """
        total = query.with_entities(func.count()).scalar()
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        }
    
    def simplePaginate(
        self,
        query: Query,
        page: int = 1,
        per_page: int = 20,
    ) -> list:
        """Simple pagination (no total count).
        
        Use when you don't need total count for better performance.
        """
        if page < 1:
            page = 1
        return query.offset((page - 1) * per_page).limit(per_page).all()


def create_query_optimizer(db: Session) -> QueryOptimizer:
    """Factory to create query optimizer."""
    return QueryOptimizer(db)


# ---- COMMON QUERY PATTERNS ----

def get_user_with_relations(db: Session, user_id: int):
    """Get user with all relationships."""
    from app.models import User
    return (
        db.query(User)
        .options(
            joinedload(User.enrollments),
            joinedload(User.submissions),
        )
        .filter(User.id == user_id)
        .first()
    )


def get_course_with_modules(db: Session, course_id: int):
    """Get course with modules and lessons."""
    from app.models import Course, Module, Lesson
    return (
        db.query(Course)
        .options(
            joinedload(Course.modules).joinedload(Module.lessons),
        )
        .filter(Course.id == course_id)
        .first()
    )


def get_class_with_students(db: Session, class_id: int):
    """Get class with enrolled students."""
    from app.models import ClassRoom, Enrollment, User
    return (
        db.query(ClassRoom)
        .options(
            joinedload(ClassRoom.enrollments).joinedload(Enrollment.user),
        )
        .filter(ClassRoom.id == class_id)
        .first()
    )


def get_assignment_with_submissions(db: Session, assignment_id: int):
    """Get assignment with all submissions."""
    from app.models import Assignment, Submission
    return (
        db.query(Assignment)
        .options(
            joinedload(Assignment.submissions),
        )
        .filter(Assignment.id == assignment_id)
        .first()
    )