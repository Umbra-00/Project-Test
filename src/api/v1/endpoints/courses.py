from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import time
import uuid

from src.data_engineering.db_utils import get_db
from src.data_collection.data_ingestion import validate_scraped_data
from src.api.v1.schemas import CourseCreate, Course
from src.api.v1 import crud  # Import the crud module
from src.utils.logging_utils import setup_logging, log_api_request
from src.core.logging_config import request_id_var
from src.api.v1 import schemas  # Import schemas for get_current_active_user
from src.api.v1.security import get_current_active_user  # Corrected import path

logger = setup_logging(__name__)

router = APIRouter()


@router.post(
    "/", summary="Ingest Course Data", tags=["Courses"], response_model=List[Course]
)
@log_api_request
async def ingest_courses(
    course_data_list: List[CourseCreate], db: Session = Depends(get_db)
):
    """
    Ingests a list of course data into the database.

    - **course_data_list**: A list of CourseCreate objects, representing courses to be ingested.
    """
    logger.info(
        f"Course ingestion request received with {len(course_data_list)} courses",
        extra={"course_count": len(course_data_list)},
    )

    if not course_data_list:
        logger.warning("Course ingestion attempted with empty data")
        raise HTTPException(status_code=400, detail="No course data provided.")

    # Validate courses
    valid_data_for_ingestion = []
    invalid_count = 0

    for course in course_data_list:
        course_dict = course.dict()
        if validate_scraped_data(course_dict):
            valid_data_for_ingestion.append(course_dict)
        else:
            invalid_count += 1
            logger.warning(
                f"Invalid course data: {course_dict.get('title', 'Unknown')}",
                extra={"course_data": course_dict},
            )

    logger.info(
        f"Course validation completed: {len(valid_data_for_ingestion)} valid, {invalid_count} invalid",
        extra={
            "valid_count": len(valid_data_for_ingestion),
            "invalid_count": invalid_count,
        },
    )

    if not valid_data_for_ingestion:
        logger.error("No valid courses found after validation")
        raise HTTPException(
            status_code=400,
            detail="No valid course data found for ingestion after validation.",
        )

    try:
        start_time = time.time()
        ingested_courses = []

        for course_data in valid_data_for_ingestion:
            # Use crud.create_course directly with a single CourseCreate object
            course_obj = crud.create_course(db, CourseCreate(**course_data))
            ingested_courses.append(course_obj)
            logger.debug(
                f"Course ingested: {course_obj.title}",
                extra={"course_id": course_obj.id, "course_url": course_obj.url},
            )

        duration = time.time() - start_time
        logger.info(
            f"Successfully ingested {len(ingested_courses)} courses",
            extra={
                "performance_metric": True,
                "ingested_count": len(ingested_courses),
                "duration_seconds": duration,
                "avg_time_per_course": (
                    duration / len(ingested_courses) if ingested_courses else 0
                ),
            },
        )

        return ingested_courses

    except HTTPException:
        raise  # Re-raise HTTPException to be handled by FastAPI
    except Exception:
        logger.error(
            "API - Unhandled error during course ingestion",
            exc_info=True,
        )
        # Let the global handler deal with this
        raise


@router.get(
    "/", summary="Get All Courses", tags=["Courses"], response_model=List[Course]
)
@log_api_request
def read_courses(
    skip: int = 0,
    limit: int = 100,
    sort_by: Optional[str] = Query(
        None, description="Field to sort by (e.g., 'title', 'difficulty')."
    ),
    sort_order: Optional[str] = Query(
        "asc", description="Sort order: 'asc' for ascending, 'desc' for descending."
    ),
    filter_criteria: Optional[str] = Query(
        None,
        description='JSON string of key-value pairs for filtering (e.g., \'{"difficulty": "Beginner"}\').',
    ),
    db: Session = Depends(get_db),
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
    logger.info(
        "Course retrieval request",
        extra={
            "skip": skip,
            "limit": limit,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "has_filters": bool(filter_criteria),
        },
    )

    # Parse filter_criteria if provided
    parsed_filter_criteria = {}
    if filter_criteria:
        try:
            parsed_filter_criteria = json.loads(filter_criteria)
            logger.debug(
                f"Filter criteria parsed successfully",
                extra={"filter_criteria": parsed_filter_criteria},
            )
        except json.JSONDecodeError as e:
            logger.error(
                f"Invalid JSON in filter_criteria: {str(e)}",
                extra={"filter_criteria_raw": filter_criteria},
            )
            raise HTTPException(
                status_code=400, detail="Invalid JSON format for filter_criteria."
            )

    try:
        start_time = time.time()
        courses = crud.get_courses(
            db,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            filter_criteria=parsed_filter_criteria,
        )

        duration = time.time() - start_time
        logger.info(
            f"Successfully retrieved {len(courses)} courses",
            extra={
                "performance_metric": True,
                "course_count": len(courses),
                "duration_seconds": duration,
                "skip": skip,
                "limit": limit,
            },
        )

        return courses

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving courses: {str(e)}",
            extra={"error_type": type(e).__name__},
            exc_info=True,
        )
        raise


@router.get(
    "/{course_url:path}",
    summary="Get Course by URL",
    tags=["Courses"],
    response_model=Course,
)
@log_api_request
def read_course_by_url(
    course_url: str = Path(..., description="The URL of the course to retrieve."),
    db: Session = Depends(get_db),
):
    """
    Retrieve a single course by its URL.

    - **course_url**: The full URL of the course.
    """
    logger.info(f"Course retrieval by URL request", extra={"course_url": course_url})

    try:
        start_time = time.time()
        db_course = crud.get_course_by_url(db, course_url)

        if db_course is None:
            logger.warning(
                f"Course not found for URL: {course_url}",
                extra={"course_url": course_url},
            )
            raise HTTPException(status_code=404, detail="Course not found.")

        duration = time.time() - start_time
        logger.info(
            f"Successfully retrieved course: {db_course.title}",
            extra={
                "performance_metric": True,
                "course_id": db_course.id,
                "course_title": db_course.title,
                "duration_seconds": duration,
            },
        )

        return db_course

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving course by URL: {str(e)}",
            extra={"course_url": course_url, "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Internal server error while retrieving course"
        )
