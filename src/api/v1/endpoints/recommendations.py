from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import time

from src.data_engineering.db_utils import get_db
from src.api.v1 import schemas  # Import schemas for type hinting
from src.api.v1.schemas import Course  # We'll need Course for the response
from src.model_development.recommendation.recommendation_model import (
    RecommendationModel,
)
from src.utils.logging_utils import setup_logging, log_api_request
from src.api.v1.exceptions import DatabaseError
from src.api.v1 import crud  # Import crud for fallback
from src.api.v1.security import get_current_active_user  # Corrected import path

logger = setup_logging(__name__)

router = APIRouter()

# Global instance of the RecommendationModel (for simplicity, in a real app, manage lifecycle)
# This model will be trained on startup or on a schedule
reco_model = RecommendationModel()


# Removed startup event - model will initialize lazily on first request

def initialize_model_if_needed(db: Session):
    """
    Initialize the recommendation model if it hasn't been initialized yet.
    This is called lazily on the first request.
    """
    global reco_model
    
    # Check if model is already initialized
    if (reco_model.tfidf_vectorizer is not None and 
        reco_model.course_vectors is not None and 
        len(reco_model.course_data) > 0):
        return True
    
    logger.info("Initializing Recommendation Model lazily...")
    start_time = time.time()
    
    try:
        # Check if database tables exist first
        try:
            # Simple test query to check if tables exist
            db.execute("SELECT 1 FROM courses LIMIT 1")
            db.commit()
            tables_exist = True
        except Exception:
            tables_exist = False
            logger.warning(
                "Database tables not yet created, skipping model initialization",
                extra={"tables_exist": False}
            )
            return False

        if not tables_exist:
            logger.info(
                "Recommendation model initialization skipped - database not ready",
                extra={"reason": "tables_not_exist"}
            )
            return False

        try:
            # Try to load existing model
            model_start = time.time()
            reco_model.load_model(db_session=db)
            model_duration = time.time() - model_start

            logger.info(
                "Recommendation Model loaded successfully",
                extra={
                    "performance_metric": True,
                    "operation": "model_load",
                    "duration_seconds": model_duration,
                },
            )
            return True
        except Exception as e:
            logger.warning(
                f"Failed to load Recommendation Model: {str(e)}",
                extra={"error_type": type(e).__name__},
                exc_info=True,
            )
            db.rollback()  # Explicitly rollback on error

            # Train model as fallback
            train_start = time.time()
            try:
                reco_model.train(db_session=db)
                train_duration = time.time() - train_start

                logger.info(
                    "Recommendation Model trained successfully as fallback",
                    extra={
                        "performance_metric": True,
                        "operation": "model_train",
                        "duration_seconds": train_duration,
                    },
                )
                return True
            except Exception as train_error:
                logger.error(
                    f"Failed to train Recommendation Model: {str(train_error)}",
                    extra={"error_type": type(train_error).__name__},
                    exc_info=True,
                )
                db.rollback()  # Explicitly rollback on error
                return False

    except Exception as init_error:
        logger.error(
            f"Model initialization failed: {str(init_error)}",
            extra={"error_type": type(init_error).__name__},
            exc_info=True,
        )
        return False


@router.post(
    "/",
    summary="Get Course Recommendations",
    response_model=List[Course],
    tags=["Recommendations"],
)
@log_api_request
async def get_course_recommendations(
    user_id: int,  # Placeholder for user ID (for future personalized recs)
    course_history_urls: Optional[List[str]] = None,
    num_recommendations: int = 5,
    db: Session = Depends(get_db),
):
    """
    Retrieves a list of recommended courses based on user history.

    - **user_id**: The ID of the user for whom to generate recommendations.
    - **course_history_urls**: A list of URLs of courses the user has interacted with (optional).
    - **num_recommendations**: The maximum number of recommendations to return.
    """
    logger.info(
        f"Recommendation request for user {user_id}",
        extra={
            "user_id": user_id,
            "history_count": len(course_history_urls) if course_history_urls else 0,
            "num_recommendations": num_recommendations,
        },
    )

    # Initialize model if needed
    if not initialize_model_if_needed(db):
        logger.warning(
            "Recommendation model could not be initialized",
            extra={
                "user_id": user_id,
                "fallback_to_popular": True,
            },
        )
        # Fallback to popular courses immediately
        fallback_start = time.time()
        popular_courses = crud.get_courses(db, limit=num_recommendations)
        fallback_duration = time.time() - fallback_start
        
        logger.info(
            f"Returned {len(popular_courses)} popular courses as fallback (model not ready)",
            extra={
                "performance_metric": True,
                "user_id": user_id,
                "course_count": len(popular_courses),
                "fallback_duration_seconds": fallback_duration,
                "reason": "model_not_ready",
            },
        )
        return popular_courses

    try:
        start_time = time.time()

        # For now, user_id is not used directly in reco_model, but for future personalization
        recommended_courses = []
        if course_history_urls:
            # Use the first URL from history for recommendation, as recommend_courses expects a single URL
            # In a full-fledged system, you'd combine recommendations from multiple history items or use a different strategy
            recommended_courses = reco_model.recommend_courses(
                course_history_urls[0], db, num_recommendations
            )

        recommendation_duration = time.time() - start_time

        if not recommended_courses:
            logger.info(
                f"No specific recommendations for user {user_id}, falling back to popular courses",
                extra={
                    "user_id": user_id,
                    "course_history_urls": course_history_urls,
                    "fallback": True,
                },
            )

            # Fallback to general popular courses
            fallback_start = time.time()
            popular_courses = crud.get_courses(db, limit=num_recommendations)
            fallback_duration = time.time() - fallback_start

            logger.info(
                f"Returned {len(popular_courses)} popular courses as fallback",
                extra={
                    "performance_metric": True,
                    "user_id": user_id,
                    "course_count": len(popular_courses),
                    "recommendation_duration_seconds": recommendation_duration,
                    "fallback_duration_seconds": fallback_duration,
                    "total_duration_seconds": time.time() - start_time,
                },
            )

            return popular_courses

        # Success with actual recommendations
        total_duration = time.time() - start_time
        logger.info(
            f"Successfully generated {len(recommended_courses)} recommendations for user {user_id}",
            extra={
                "performance_metric": True,
                "user_id": user_id,
                "recommendation_count": len(recommended_courses),
                "duration_seconds": total_duration,
                "course_history_count": (
                    len(course_history_urls) if course_history_urls else 0
                ),
            },
        )

        return recommended_courses

    except DatabaseError as e:
        logger.error(
            f"Database error in recommendations: {str(e)}",
            extra={"user_id": user_id, "error_type": type(e).__name__},
        )
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    except Exception as e:
        logger.error(
            f"Error generating recommendations for user {user_id}: {str(e)}",
            extra={
                "user_id": user_id,
                "error_type": type(e).__name__,
                "course_history_urls": course_history_urls,
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations.",
        )
