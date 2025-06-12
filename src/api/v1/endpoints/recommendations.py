from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from src.data_engineering.db_utils import get_db
from src.api.v1.schemas import Course, User, CourseCreate # We'll need Course for the response
from src.model_development.recommendation.recommendation_model import RecommendationModel
from src.utils.logging_utils import setup_logging
from src.api.v1.exceptions import DatabaseError, NotFoundError
from src.api.v1 import crud # Import crud for fallback

logger = setup_logging(__name__)

router = APIRouter()

# Global instance of the RecommendationModel (for simplicity, in a real app, manage lifecycle)
# This model will be trained on startup or on a schedule
reco_model = RecommendationModel()

@router.on_event("startup")
async def startup_event():
    logger.info("Initializing Recommendation Model on startup...")
    with next(get_db()) as db:
        try:
            reco_model.load_model(db_session=db) # Attempt to load the model
            logger.info("Recommendation Model loaded successfully on startup.")
        except Exception as e:
            logger.warning(f"Failed to load Recommendation Model on startup: {e}. Attempting to train instead.")
            reco_model.train(db_session=db)
            logger.info("Recommendation Model trained successfully as fallback.")

        # After attempting to load or train, always ensure the model is up-to-date with latest data
        # This provides a simple continuous training mechanism upon application startup.
        reco_model.retrain_model_if_needed(db_session=db)

@router.post("/", summary="Get Course Recommendations", response_model=List[Course], tags=["Recommendations"])
async def get_course_recommendations(
    user_id: int, # Placeholder for user ID (for future personalized recs)
    course_history_urls: Optional[List[str]] = None,
    num_recommendations: int = 5,
    db: Session = Depends(get_db)
):
    """
    Retrieves a list of recommended courses based on user history.

    - **user_id**: The ID of the user for whom to generate recommendations.
    - **course_history_urls**: A list of URLs of courses the user has interacted with (optional).
    - **num_recommendations**: The maximum number of recommendations to return.
    """
    if not reco_model.tfidf_vectorizer or not reco_model.course_embeddings or not reco_model.courses_df:
        logger.warning("Recommendation model not fully trained or loaded. Cannot provide recommendations.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Recommendation model not yet trained or loaded.")

    try:
        # For now, user_id is not used directly in reco_model, but for future personalization
        recommended_courses = reco_model.recommend_courses(course_history_urls or [], db, num_recommendations)
        if not recommended_courses:
            logger.info(f"No specific recommendations for user {user_id} with history {course_history_urls}. Providing general popular courses.")
            return crud.get_courses(db, limit=num_recommendations) # Fallback to general popular courses
            
        return recommended_courses
    except DatabaseError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"Error generating recommendations for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate recommendations.") 