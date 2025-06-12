from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json

from src.data_engineering.db_utils import get_db
from src.data_collection.data_ingestion import ingest_course_data_batch, validate_scraped_data
from src.api.v1.schemas import CourseCreate, Course
from src.api.v1 import crud # Import the crud module
from src.utils.logging_utils import setup_logging

logger = setup_logging(__name__)

router = APIRouter()

@router.post("/", summary="Ingest Course Data", tags=["Courses"], response_model=List[Course])
async def ingest_courses(course_data_list: List[CourseCreate], db: Session = Depends(get_db)):
    """
    Ingests a list of course data into the database.

    - **course_data_list**: A list of CourseCreate objects, representing courses to be ingested.
    """
    if not course_data_list:
        raise HTTPException(status_code=400, detail="No course data provided.")

    valid_data_for_ingestion = [
        course.dict() for course in course_data_list if validate_scraped_data(course.dict())
    ]

    if not valid_data_for_ingestion:
        raise HTTPException(status_code=400, detail="No valid course data found for ingestion after validation.")

    try:
        ingested_courses = []
        for course_data in valid_data_for_ingestion:
            # Use crud.create_course directly with a single CourseCreate object
            course_obj = crud.create_course(db, CourseCreate(**course_data))
            ingested_courses.append(course_obj)
        return ingested_courses
    except Exception as e:
        logger.error(f"API - Error during course ingestion: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error during ingestion: {e}")

@router.get("/", summary="Get All Courses", tags=["Courses"], response_model=List[Course])
def read_courses(
    skip: int = 0,
    limit: int = 100,
    sort_by: Optional[str] = Query(None, description="Field to sort by (e.g., 'title', 'difficulty')."),
    sort_order: Optional[str] = Query("asc", description="Sort order: 'asc' for ascending, 'desc' for descending."),
    filter_criteria: Optional[str] = Query(None, description="JSON string of key-value pairs for filtering (e.g., '{\"difficulty\": \"Beginner\"}')."),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of courses with optional pagination, filtering, and sorting.

    - **skip**: Number of records to skip (for pagination).
    - **limit**: Maximum number of records to return.
    - **sort_by**: Optional field to sort the results by (e.g., 'title', 'difficulty').
    - **sort_order**: Optional sort order ('asc' for ascending, 'desc' for descending). Defaults to 'asc'.
    - **filter_criteria**: Optional JSON string containing key-value pairs for filtering.
      Example: `{\"difficulty\": \"Beginner\", \"category\": \"Programming\"}`.
    """
    # Parse filter_criteria if provided
    parsed_filter_criteria = {}
    if filter_criteria:
        try:
            parsed_filter_criteria = json.loads(filter_criteria)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format for filter_criteria.")

    courses = crud.get_courses(
        db,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        filter_criteria=parsed_filter_criteria
    )
    return courses

@router.get("/{course_url:path}", summary="Get Course by URL", tags=["Courses"], response_model=Course)
def read_course_by_url(course_url: str = Path(..., description="The URL of the course to retrieve."), db: Session = Depends(get_db)):
    """
    Retrieve a single course by its URL.

    - **course_url**: The full URL of the course.
    """
    db_course = crud.get_course_by_url(db, course_url)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Course not found.")
    return db_course 