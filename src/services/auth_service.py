# Copyright (c) 2024 Umbra. All rights reserved.
"""
Authentication Service for Umbra Personalized Learning Platform
Handles user registration, login, profile management, and business logic
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.data_engineering.database_models import User, Course, LearningProgress, SkillAssessment, UserLearningPath
from src.api.v1 import schemas
from src.utils.auth_utils import get_password_hash, verify_password
from src.api.v1.security import create_access_token
from src.utils.logging_utils import setup_logging

logger = setup_logging(__name__)


class AuthService:
    """Comprehensive authentication and user management service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def register_user(self, user_data: schemas.UserCreate) -> schemas.User:
        """Register a new user with comprehensive profile setup"""
        try:
            # Check if user already exists
            existing_user = self.db.query(User).filter(
                User.user_identifier == user_data.user_identifier
            ).first()
            
            if existing_user:
                raise ValueError("User already exists with this identifier")
            
            # Create user with hashed password
            hashed_password = get_password_hash(user_data.password)
            
            # Create user with personalization data
            db_user = User(
                user_identifier=user_data.user_identifier,
                password_hash=hashed_password,
                role="student",  # Default role
                registration_date=datetime.utcnow(),
                learning_goals=user_data.learning_goals,
                current_skill_level=user_data.current_skill_level or "beginner",
                preferred_learning_style=user_data.preferred_learning_style or "mixed",
                time_availability=user_data.time_availability or "medium",
                career_field=user_data.career_field
            )
            
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            
            logger.info(f"User registered successfully: {user_data.user_identifier}")
            return schemas.User.model_validate(db_user)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error registering user: {str(e)}")
            raise
    
    def authenticate_user(self, user_identifier: str, password: str) -> Optional[User]:
        """Authenticate user and return user object if valid"""
        try:
            user = self.db.query(User).filter(
                User.user_identifier == user_identifier
            ).first()
            
            if not user:
                logger.warning(f"Authentication failed: User not found - {user_identifier}")
                return None
            
            if not verify_password(password, user.password_hash):
                logger.warning(f"Authentication failed: Invalid password - {user_identifier}")
                return None
            
            # Update last login
            user.last_login = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"User authenticated successfully: {user_identifier}")
            return user
            
        except Exception as e:
            logger.error(f"Error during authentication: {str(e)}")
            return None
    
    def login_user(self, user_identifier: str, password: str) -> Optional[schemas.Token]:
        """Login user and return access token"""
        user = self.authenticate_user(user_identifier, password)
        if not user:
            return None
        
        # Create access token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user.user_identifier, "role": user.role},
            expires_delta=access_token_expires
        )
        
        return schemas.Token(
            access_token=access_token,
            token_type="bearer"
        )
    
    def get_user_profile(self, user_id: int) -> Optional[schemas.User]:
        """Get comprehensive user profile"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            return schemas.User.model_validate(user)
            
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return None
    
    def update_user_profile(self, user_id: int, profile_data: schemas.UserUpdate) -> Optional[schemas.User]:
        """Update user profile with personalization data"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            # Update fields if provided
            if profile_data.learning_goals is not None:
                user.learning_goals = profile_data.learning_goals
            if profile_data.current_skill_level is not None:
                user.current_skill_level = profile_data.current_skill_level
            if profile_data.preferred_learning_style is not None:
                user.preferred_learning_style = profile_data.preferred_learning_style
            if profile_data.time_availability is not None:
                user.time_availability = profile_data.time_availability
            if profile_data.career_field is not None:
                user.career_field = profile_data.career_field
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"User profile updated: {user.user_identifier}")
            return schemas.User.model_validate(user)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user profile: {str(e)}")
            return None
    
    def get_user_dashboard_data(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive dashboard data for user"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {}
            
            # Get learning progress
            progress = self.db.query(LearningProgress).filter(
                LearningProgress.user_id == user_id
            ).all()
            
            # Get skill assessments
            skills = self.db.query(SkillAssessment).filter(
                SkillAssessment.user_id == user_id
            ).all()
            
            # Get active learning paths
            learning_paths = self.db.query(UserLearningPath).filter(
                and_(
                    UserLearningPath.user_id == user_id,
                    UserLearningPath.is_completed == False
                )
            ).all()
            
            # Calculate statistics
            total_courses = len(progress)
            completed_courses = len([p for p in progress if p.is_completed])
            total_time_spent = sum(p.time_spent_seconds for p in progress)
            
            dashboard_data = {
                "user_profile": schemas.User.model_validate(user),
                "learning_stats": {
                    "total_courses": total_courses,
                    "completed_courses": completed_courses,
                    "completion_rate": (completed_courses / total_courses * 100) if total_courses > 0 else 0,
                    "total_time_spent_hours": total_time_spent / 3600,
                    "active_learning_paths": len(learning_paths)
                },
                "recent_progress": [
                    {
                        "course_id": p.course_id,
                        "progress_percentage": p.progress_percentage,
                        "last_accessed": p.last_accessed,
                        "is_completed": p.is_completed
                    } for p in sorted(progress, key=lambda x: x.last_accessed, reverse=True)[:5]
                ],
                "skills": [
                    {
                        "skill_name": s.skill_name,
                        "skill_level": s.skill_level,
                        "score": s.score,
                        "assessment_date": s.assessment_date
                    } for s in skills
                ]
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            return {}
    
    def get_personalized_course_recommendations(self, user_id: int, limit: int = 5) -> list:
        """Get personalized course recommendations based on user profile"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return []
            
            # Get user's current courses to avoid duplicates
            user_courses = self.db.query(LearningProgress.course_id).filter(
                LearningProgress.user_id == user_id
            ).subquery()
            
            # Basic recommendation logic based on user profile
            query = self.db.query(Course).filter(
                Course.id.notin_(user_courses)
            )
            
            # Filter by skill level
            if user.current_skill_level:
                query = query.filter(Course.difficulty_level == user.current_skill_level)
            
            # Filter by career field if specified
            if user.career_field:
                query = query.filter(
                    or_(
                        Course.category.ilike(f"%{user.career_field}%"),
                        Course.title.ilike(f"%{user.career_field}%")
                    )
                )
            
            recommendations = query.limit(limit).all()
            
            return [
                {
                    "type": "course",
                    "id": course.id,
                    "title": course.title,
                    "description": course.description,
                    "category": course.category,
                    "difficulty_level": course.difficulty_level,
                    "match_score": 0.8,  # Placeholder - would be calculated by ML model
                    "reason": f"Recommended based on your {user.current_skill_level} skill level and {user.career_field} career interest"
                }
                for course in recommendations
            ]
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            return []
    
    def record_user_interaction(self, user_id: int, interaction_type: str, content_id: Optional[int] = None, details: Optional[str] = None):
        """Record user interaction for analytics and recommendation improvement"""
        try:
            from src.data_engineering.database_models import Interaction
            
            interaction = Interaction(
                user_id=user_id,
                content_id=content_id,
                interaction_type=interaction_type,
                timestamp=datetime.utcnow(),
                details=details
            )
            
            self.db.add(interaction)
            self.db.commit()
            
            logger.info(f"User interaction recorded: {user_id} - {interaction_type}")
            
        except Exception as e:
            logger.error(f"Error recording interaction: {str(e)}")
    
    def get_user_business_data(self, user_id: int) -> Dict[str, Any]:
        """Get business-specific data for user (for different organizations/datasets)"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {}
            
            # This could be extended to handle different business contexts
            # For now, return basic user segmentation data
            
            learning_progress = self.db.query(LearningProgress).filter(
                LearningProgress.user_id == user_id
            ).all()
            
            # Calculate user segment based on activity
            total_courses = len(learning_progress)
            completed_courses = len([p for p in learning_progress if p.is_completed])
            
            if total_courses == 0:
                user_segment = "new_user"
            elif completed_courses / total_courses >= 0.8:
                user_segment = "high_performer"
            elif completed_courses / total_courses >= 0.5:
                user_segment = "active_learner"
            else:
                user_segment = "struggling_learner"
            
            return {
                "user_segment": user_segment,
                "engagement_level": "high" if total_courses > 10 else "medium" if total_courses > 3 else "low",
                "learning_velocity": completed_courses / max(1, total_courses),
                "preferred_difficulty": user.current_skill_level,
                "career_focus": user.career_field,
                "learning_style": user.preferred_learning_style,
                "time_commitment": user.time_availability
            }
            
        except Exception as e:
            logger.error(f"Error getting business data: {str(e)}")
            return {}
