# Copyright (c) 2024 Umbra. All rights reserved.
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from src.data_engineering.db_utils import check_db_health
from src.utils.logging_utils import setup_logging
from src.api.v1.endpoints import courses, recommendations, users, learning_paths  # Import routers
from src.api.v1.exceptions import (
    DatabaseError,
    NotFoundError,
    ConflictError,
)  # Import custom exceptions

# Setup logging for the API
logger = setup_logging(__name__)

app = FastAPI(
    title="Educational Data Science Platform API",
    description="API for managing educational content, learning progress, and recommendations.",
    version="1.0.0",
    root_path="/api/v1",  # Explicitly set the root path for the application
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include routers for different API functionalities.
app.include_router(courses.router, prefix="/courses", tags=["Courses"])
app.include_router(
    recommendations.router, prefix="/recommendations", tags=["Recommendations"]
)
app.include_router(users.router, tags=["Users"])  # Include the users router
app.include_router(learning_paths.router, prefix="/learning-paths", tags=["Learning Paths"])  # Include the learning paths router


# --- Global Exception Handlers ---
@app.exception_handler(DatabaseError)
async def database_exception_handler(request: Request, exc: DatabaseError):
    logger.error(f"Database Error occurred: {exc.detail}", exc_info=True)
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail, "code": "database_error"},
    )


@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request: Request, exc: NotFoundError):
    logger.warning(f"Resource not found: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail, "code": "not_found"},
    )


@app.exception_handler(ConflictError)
async def conflict_exception_handler(request: Request, exc: ConflictError):
    logger.warning(f"Conflict error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail, "code": "conflict_error"},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(
        f"HTTP Exception occurred: {exc.detail} (Status: {exc.status_code})",
        exc_info=True,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail, "code": "http_error"},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.critical(f"An unhandled error occurred: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "An unexpected error occurred.", "code": "server_error"},
    )


# --- End Global Exception Handlers ---


@app.get("/health", summary="Health Check", tags=["Monitoring"])
def health_check():
    """
    Performs a health check on the API and its dependencies.
    Returns 200 if the API is up and the database connection is healthy.
    """
    if check_db_health():
        return {"status": "healthy", "database_connection": "successful"}
    else:
        # This will now be caught by the DatabaseError handler if it's a DB issue
        # or a generic HTTPException if check_db_health() raises a different HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed",
        )


# Remove redundant ingest-courses endpoint from main.py, as it's defined in courses.py
# @app.post("/ingest-courses", summary="Ingest Course Data", tags=["Data Ingestion"])
# async def ingest_courses(course_data_list: List[CourseCreate], db: Session = Depends(get_db)):
#     """
#     Ingests a list of course data into the database.

#     - **course_data_list**: A list of CourseCreate objects, representing courses to be ingested.
#     """
#     if not course_data_list:
#         raise HTTPException(status_code=400, detail="No course data provided.")

#     valid_data_for_ingestion = [
#         course.dict() for course in course_data_list if validate_scraped_data(course.dict())
#     ]

#     if not valid_data_for_ingestion:
#         raise HTTPException(status_code=400, detail="No valid course data found for ingestion after validation.")

#     try:
#         ingest_course_data_batch(valid_data_for_ingestion, db)
#         return {"status": "success", "message": f"Attempted to ingest {len(valid_data_for_ingestion)} valid courses."}
#     except Exception as e:
#         logger.error(f"API - Error during course ingestion: {e}")
#         raise HTTPException(status_code=500, detail=f"Internal server error during ingestion: {e}")

# You can add more endpoints here for other workflows (e.g., user management, content retrieval, etc.)

# This is a test comment for reload functionality

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting FastAPI application...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
