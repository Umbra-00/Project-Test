# Copyright (c) 2024 Umbra. All rights reserved.
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from src.data_engineering.db_utils import get_db
from src.api.v1 import crud, schemas
from src.api.v1.security import get_current_user
from src.utils.logging_utils import setup_logging

logger = setup_logging(__name__)

router = APIRouter()


@router.get("/", response_model=List[schemas.LearningPath])
def get_learning_paths(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    difficulty_level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve learning paths with optional filtering.
    """
    try:
        learning_paths = crud.get_learning_paths(
            db, skip=skip, limit=limit, category=category, difficulty_level=difficulty_level
        )
        return learning_paths
    except Exception as e:
        logger.error(f"Error fetching learning paths: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch learning paths"
        )


@router.post("/", response_model=schemas.LearningPath)
def create_learning_path(
    learning_path: schemas.LearningPathCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    """
    Create a new learning path.
    """
    try:
        db_learning_path = crud.create_learning_path(
            db=db, learning_path=learning_path, creator_id=current_user.id
        )
        return db_learning_path
    except Exception as e:
        logger.error(f"Error creating learning path: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create learning path"
        )


@router.get("/{path_id}", response_model=schemas.LearningPathWithCourses)
def get_learning_path(path_id: int, db: Session = Depends(get_db)):
    """
    Get a specific learning path with its courses.
    """
    learning_path = crud.get_learning_path_with_courses(db, path_id)
    if learning_path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning path not found"
        )
    return learning_path


@router.post("/{path_id}/enroll", response_model=schemas.UserLearningPath)
def enroll_in_learning_path(
    path_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    """
    Enroll the current user in a learning path.
    """
    try:
        # Check if learning path exists
        learning_path = crud.get_learning_path(db, path_id)
        if not learning_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learning path not found"
            )
        
        # Check if user is already enrolled
        existing_enrollment = crud.get_user_learning_path(db, current_user.id, path_id)
        if existing_enrollment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already enrolled in this learning path"
            )
        
        # Enroll user
        enrollment = crud.enroll_user_in_learning_path(db, current_user.id, path_id)
        return enrollment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enrolling user in learning path: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enroll in learning path"
        )


@router.get("/user/{user_id}/paths", response_model=List[schemas.UserLearningPath])
def get_user_learning_paths(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    """
    Get all learning paths for a specific user.
    """
    # Users can only view their own paths unless they're admin
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these learning paths"
        )
    
    try:
        user_paths = crud.get_user_learning_paths(db, user_id)
        return user_paths
    except Exception as e:
        logger.error(f"Error fetching user learning paths: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user learning paths"
        )


@router.put("/user/{user_id}/paths/{path_id}/progress")
def update_learning_path_progress(
    user_id: int,
    path_id: int,
    progress_percentage: float,
    current_course_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    """
    Update progress for a user's learning path.
    """
    # Users can only update their own progress unless they're admin
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this progress"
        )
    
    try:
        updated_path = crud.update_learning_path_progress(
            db, user_id, path_id, progress_percentage, current_course_id
        )
        if not updated_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User learning path not found"
            )
        return {"message": "Progress updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating learning path progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update progress"
        )
