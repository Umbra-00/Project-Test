# Copyright (c) 2024 Umbra. All rights reserved.
from pydantic import BaseModel, HttpUrl, ConfigDict, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    user_identifier: str  # This will be the user-provided unique ID


class UserCreate(BaseModel):
    username: str
    learning_goals: Optional[str] = None  # JSON string with goals
    current_skill_level: Optional[str] = None  # 'beginner', 'intermediate', 'advanced'
    preferred_learning_style: Optional[str] = None  # 'visual', 'auditory', 'kinesthetic', 'mixed'
    time_availability: Optional[str] = None  # 'low', 'medium', 'high'
    career_field: Optional[str] = None  # Target career field


class User(UserBase):
    id: int
    role: str
    registration_date: datetime
    last_login: Optional[datetime] = None
    learning_preferences: Optional[str] = None
    learning_goals: Optional[str] = None
    current_skill_level: Optional[str] = None
    preferred_learning_style: Optional[str] = None
    time_availability: Optional[str] = None
    career_field: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    url: str  # Changed from HttpUrl
    instructor: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    difficulty_level: Optional[str] = None  # Aligned with database model
    category: Optional[str] = None
    platform: Optional[str] = None


class CourseCreate(BaseModel):
    title: str
    description: str
    url: str  # Changed from HttpUrl
    instructor: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    difficulty_level: Optional[str] = None
    category: Optional[str] = None
    platform: Optional[str] = None


class Course(CourseBase):
    id: int
    created_by_user_id: Optional[int] = None
    creation_date: datetime
    ai_generated_version: int

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_identifier: Optional[str] = None  # Renamed from username


# Learning Path Schemas
class LearningPathBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    difficulty_level: Optional[str] = None
    estimated_duration_hours: Optional[int] = None


class LearningPathCreate(LearningPathBase):
    course_ids: list[int] = []  # List of course IDs to include in the path


class LearningPath(LearningPathBase):
    id: int
    created_by_user_id: Optional[int] = None
    creation_date: datetime
    is_active: bool = True
    
    model_config = ConfigDict(from_attributes=True)


class LearningPathWithCourses(LearningPath):
    courses: list[Course] = []


# User Learning Path Schemas
class UserLearningPathBase(BaseModel):
    learning_path_id: int


class UserLearningPathCreate(UserLearningPathBase):
    pass


class UserLearningPath(UserLearningPathBase):
    id: int
    user_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    is_completed: bool = False
    current_course_id: Optional[int] = None
    progress_percentage: float = 0.0
    
    model_config = ConfigDict(from_attributes=True)


# Skill Assessment Schemas
class SkillAssessmentBase(BaseModel):
    skill_name: str
    skill_level: str  # 'beginner', 'intermediate', 'advanced'
    score: Optional[float] = None
    assessment_type: Optional[str] = None  # 'self-reported', 'quiz', 'project', 'peer-review'
    evidence_url: Optional[str] = None


class SkillAssessmentCreate(SkillAssessmentBase):
    pass


class SkillAssessment(SkillAssessmentBase):
    id: int
    user_id: int
    assessment_date: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Personalized Recommendation Request
class PersonalizedRecommendationRequest(BaseModel):
    user_id: int
    max_recommendations: int = 5
    preferred_difficulty: Optional[str] = None
    preferred_category: Optional[str] = None
    include_learning_paths: bool = True


# Personalized Recommendation Response
class PersonalizedRecommendation(BaseModel):
    type: str  # 'course' or 'learning_path'
    id: int
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    difficulty_level: Optional[str] = None
    match_score: float  # 0.0 to 1.0
    reason: str  # Why this was recommended
    estimated_duration: Optional[int] = None  # in hours
