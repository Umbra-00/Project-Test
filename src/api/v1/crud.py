from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from src.data_engineering.database_models import Course
from src.api.v1.schemas import CourseCreate
from src.api.v1.exceptions import DatabaseError, NotFoundError, ConflictError
from typing import List, Optional, Dict, Any

def create_course(db: Session, course: CourseCreate) -> Course:
    try:
        db_course = Course(title=course.title, description=course.description, url=course.url)
        db.add(db_course)
        db.commit()
        db.refresh(db_course)
        return db_course
    except IntegrityError as e:
        db.rollback()
        raise ConflictError(detail=f"Course with URL {course.url} already exists.") from e
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
    filter_criteria: Optional[Dict[str, Any]] = None
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
                    pass # Silently ignore invalid filter fields for now

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
                pass # Silently ignore invalid sort fields for now

        return query.offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        raise DatabaseError(detail=f"Could not retrieve courses: {e}") from e 