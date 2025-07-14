from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from src.data_engineering.db_utils import get_db
from src.api.v1.security import get_current_active_user
from src.api.v1 import schemas
from src.services.auth_service import AuthService
from src.data_engineering.database_models import User, Course, LearningProgress, SkillAssessment
from src.utils.logging_utils import setup_logging

router = APIRouter()
logger = setup_logging(__name__)


@router.get("/user-analytics", summary="Get user analytics for business intelligence")
def get_user_analytics(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    """Get comprehensive user analytics for business intelligence"""
    try:
        auth_service = AuthService(db)
        
        # Get user business data
        business_data = auth_service.get_user_business_data(current_user.id)
        
        # Get dashboard data
        dashboard_data = auth_service.get_user_dashboard_data(current_user.id)
        
        # Get personalized recommendations
        recommendations = auth_service.get_personalized_course_recommendations(current_user.id, limit=10)
        
        return {
            "user_id": current_user.id,
            "user_identifier": current_user.user_identifier,
            "business_intelligence": business_data,
            "dashboard_data": dashboard_data,
            "recommendations": recommendations,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error getting user analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/personalized-dataset", summary="Get personalized dataset for user")
def get_personalized_dataset(
    include_progress: bool = Query(True, description="Include learning progress data"),
    include_skills: bool = Query(True, description="Include skill assessment data"),
    include_interactions: bool = Query(False, description="Include interaction data"),
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    """Get personalized dataset based on user's learning history and preferences"""
    try:
        dataset = {
            "user_profile": {
                "id": current_user.id,
                "user_identifier": current_user.user_identifier,
                "role": current_user.role,
                "learning_goals": current_user.learning_goals,
                "current_skill_level": current_user.current_skill_level,
                "preferred_learning_style": current_user.preferred_learning_style,
                "time_availability": current_user.time_availability,
                "career_field": current_user.career_field,
                "registration_date": current_user.registration_date,
                "last_login": current_user.last_login
            }
        }
        
        if include_progress:
            progress_data = db.query(LearningProgress).filter(
                LearningProgress.user_id == current_user.id
            ).all()
            
            dataset["learning_progress"] = [
                {
                    "course_id": p.course_id,
                    "progress_percentage": p.progress_percentage,
                    "last_accessed": p.last_accessed,
                    "completed_at": p.completed_at,
                    "is_completed": p.is_completed,
                    "time_spent_seconds": p.time_spent_seconds
                } for p in progress_data
            ]
        
        if include_skills:
            skill_data = db.query(SkillAssessment).filter(
                SkillAssessment.user_id == current_user.id
            ).all()
            
            dataset["skill_assessments"] = [
                {
                    "skill_name": s.skill_name,
                    "skill_level": s.skill_level,
                    "score": s.score,
                    "assessment_date": s.assessment_date,
                    "assessment_type": s.assessment_type,
                    "evidence_url": s.evidence_url
                } for s in skill_data
            ]
        
        if include_interactions:
            from src.data_engineering.database_models import Interaction
            interaction_data = db.query(Interaction).filter(
                Interaction.user_id == current_user.id
            ).order_by(Interaction.timestamp.desc()).limit(100).all()
            
            dataset["interactions"] = [
                {
                    "content_id": i.content_id,
                    "interaction_type": i.interaction_type,
                    "timestamp": i.timestamp,
                    "details": i.details
                } for i in interaction_data
            ]
        
        return dataset
        
    except Exception as e:
        logger.error(f"Error getting personalized dataset: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/user-segments", summary="Get user segmentation data")
def get_user_segments(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    """Get user segmentation data for business analysis"""
    try:
        auth_service = AuthService(db)
        business_data = auth_service.get_user_business_data(current_user.id)
        
        # Get all users for comparison (admin only in real implementation)
        if current_user.role == "admin":
            all_users = db.query(User).all()
            user_segments = {}
            
            for user in all_users:
                user_biz_data = auth_service.get_user_business_data(user.id)
                segment = user_biz_data.get("user_segment", "unknown")
                
                if segment not in user_segments:
                    user_segments[segment] = []
                
                user_segments[segment].append({
                    "user_id": user.id,
                    "user_identifier": user.user_identifier,
                    "engagement_level": user_biz_data.get("engagement_level", "unknown"),
                    "learning_velocity": user_biz_data.get("learning_velocity", 0),
                    "career_focus": user_biz_data.get("career_focus", "unknown")
                })
            
            return {
                "current_user_segment": business_data.get("user_segment", "unknown"),
                "all_segments": user_segments,
                "segment_counts": {segment: len(users) for segment, users in user_segments.items()}
            }
        else:
            return {
                "current_user_segment": business_data.get("user_segment", "unknown"),
                "engagement_level": business_data.get("engagement_level", "unknown"),
                "learning_velocity": business_data.get("learning_velocity", 0)
            }
            
    except Exception as e:
        logger.error(f"Error getting user segments: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/learning-insights", summary="Get learning insights for user")
def get_learning_insights(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    """Get detailed learning insights and analytics"""
    try:
        # Get user's learning progress
        progress_data = db.query(LearningProgress).filter(
            LearningProgress.user_id == current_user.id
        ).all()
        
        if not progress_data:
            return {
                "message": "No learning data available yet",
                "suggestions": [
                    "Start by enrolling in a course that matches your skill level",
                    "Complete your profile to get personalized recommendations",
                    "Take a skill assessment to help us understand your current level"
                ]
            }
        
        # Calculate insights
        total_courses = len(progress_data)
        completed_courses = len([p for p in progress_data if p.is_completed])
        total_time_spent = sum(p.time_spent_seconds for p in progress_data)
        avg_progress = sum(p.progress_percentage for p in progress_data) / total_courses
        
        # Learning velocity (courses completed per week since registration)
        registration_date = current_user.registration_date
        weeks_since_registration = (datetime.utcnow() - registration_date).days / 7
        learning_velocity = completed_courses / max(1, weeks_since_registration)
        
        # Most active learning times
        recent_activity = [p for p in progress_data if p.last_accessed and 
                          p.last_accessed > datetime.utcnow() - timedelta(days=30)]
        
        insights = {
            "learning_summary": {
                "total_courses_enrolled": total_courses,
                "courses_completed": completed_courses,
                "completion_rate": (completed_courses / total_courses * 100) if total_courses > 0 else 0,
                "total_time_spent_hours": total_time_spent / 3600,
                "average_progress": avg_progress,
                "learning_velocity_courses_per_week": learning_velocity
            },
            "learning_patterns": {
                "preferred_difficulty": current_user.current_skill_level,
                "learning_style": current_user.preferred_learning_style,
                "time_availability": current_user.time_availability,
                "career_focus": current_user.career_field,
                "recent_activity_last_30_days": len(recent_activity)
            },
            "recommendations": [
                "Continue focusing on your current skill level courses" if avg_progress > 70 else "Consider reviewing fundamentals",
                "Try to maintain consistent learning schedule" if learning_velocity > 0.5 else "Set aside regular time for learning",
                "Explore courses in your career field" if current_user.career_field else "Consider defining your career goals"
            ]
        }
        
        return insights
        
    except Exception as e:
        logger.error(f"Error getting learning insights: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/record-interaction", summary="Record user interaction for analytics")
def record_user_interaction(
    interaction_type: str,
    content_id: Optional[int] = None,
    details: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    """Record user interaction for analytics and recommendation improvement"""
    try:
        auth_service = AuthService(db)
        auth_service.record_user_interaction(
            user_id=current_user.id,
            interaction_type=interaction_type,
            content_id=content_id,
            details=details
        )
        
        return {
            "status": "success",
            "message": "Interaction recorded successfully",
            "interaction_type": interaction_type,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error recording interaction: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

