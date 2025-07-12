from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from src.data_engineering.database_models import Course, User
from src.api.v1.schemas import CourseCreate, UserCreate
from src.api.v1.exceptions import DatabaseError, ConflictError
from typing import List, Optional, Dict, Any
from src.utils.auth_utils import get_password_hash
from src.utils.logging_utils import setup_logging, log_database_operation, log_security_event
import time

logger = setup_logging(__name__)


def create_course(db: Session, course: CourseCreate) -> Course:
    try:
        db_course = Course(
            title=course.title,
            description=course.description,
            url=str(course.url),  # Ensure HttpUrl is converted to string
            instructor=course.instructor,
            price=course.price,
            currency=course.currency,
            difficulty_level=course.difficulty_level,
            category=course.category,
            platform=course.platform,
        )
        db.add(db_course)
        db.commit()
        db.refresh(db_course)
        return db_course
    except IntegrityError as e:
        db.rollback()
        raise ConflictError(
            detail=f"Course with URL {course.url} already exists."
        ) from e
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseError(detail=f"Could not create course: {e}") from e


def get_course_by_url(db: Session, url: str) -> Course | None:
    try:
        return db.query(Course).filter(Course.url == url).first()
    except SQLAlchemyError as e:
        raise DatabaseError(detail=f"Could not retrieve course by URL: {e}") from e


def get_courses(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    filter_criteria: Optional[Dict[str, Any]] = None,
) -> List[Course]:
    try:
        query = db.query(Course)

        if filter_criteria:
            for field, value in filter_criteria.items():
                # Basic filtering: assumes exact match for simplicity.
                # For more complex filtering (e.g., partial matches, range),
                # additional logic would be needed.
                if hasattr(Course, field):
                    query = query.filter(getattr(Course, field) == value)
                else:
                    # Optionally raise an error for invalid filter fields
                    # Or log a warning
                    pass  # Silently ignore invalid filter fields for now

        if sort_by:
            # Basic sorting: assumes field exists in Course model.
            # For more complex sorting (e.g., case-insensitive),
            # additional logic would be needed.
            if hasattr(Course, sort_by):
                if sort_order == "desc":
                    query = query.order_by(getattr(Course, sort_by).desc())
                else:
                    query = query.order_by(getattr(Course, sort_by).asc())
            else:
                # Optionally raise an error for invalid sort fields
                # Or log a warning
                pass  # Silently ignore invalid sort fields for now

        return query.offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        raise DatabaseError(detail=f"Could not retrieve courses: {e}") from e


# --- User CRUD Operations ---
def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        user_identifier=user.user_identifier,
        password_hash=hashed_password,
        role="student",
    )  # Default role to student
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_user_identifier(db: Session, user_identifier: str):
    return db.query(User).filter(User.user_identifier == user_identifier).first()


def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()
