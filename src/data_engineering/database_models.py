# Copyright (c) 2024 [Your Name/Company]. All rights reserved.
# src/data_engineering/database_models.py
# Defines the SQLAlchemy ORM models for the learning platform database schema.

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey, Index
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False) # Store hashed passwords
    role = Column(String, default='student', nullable=False) # 'student', 'instructor', 'admin'
    registration_date = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    learning_preferences = Column(Text) # JSON or similar for structured preferences

    # Relationships
    progress = relationship("LearningProgress", back_populates="user")
    interactions = relationship("Interaction", back_populates="user")

    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_email', 'email'),
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"

class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    url = Column(String, unique=True, nullable=True) # Added URL column
    created_by_user_id = Column(Integer, ForeignKey('users.id')) # Instructor/Admin who created it
    creation_date = Column(DateTime, default=datetime.utcnow)
    difficulty_level = Column(String) # 'beginner', 'intermediate', 'advanced'
    ai_generated_version = Column(Integer, default=1) # For tracking AI content versions

    # Relationships
    creator = relationship("User")
    contents = relationship("Content", back_populates="course")
    assessments = relationship("Assessment", back_populates="course")
    learning_progress = relationship("LearningProgress", back_populates="course")

    __table_args__ = (
        Index('idx_course_url', 'url'),
        Index('idx_course_title', 'title'),
    )

    def __repr__(self):
        return f"<Course(id={self.id}, title='{self.title}')>"

class Content(Base):
    __tablename__ = 'content'
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    title = Column(String, nullable=False)
    content_type = Column(String, nullable=False) # 'text', 'video', 'quiz', 'article'
    body = Column(Text) # Actual content (text, or path to file/resource)
    embedding_vector = Column(Text) # Store as JSON string or array, for similarity search
    version = Column(Integer, default=1) # Version of the content (e.g., if AI revises it)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    course = relationship("Course", back_populates="contents")
    interactions = relationship("Interaction", back_populates="content")

    __table_args__ = (
        Index('idx_content_course_id', 'course_id'),
    )

    def __repr__(self):
        return f"<Content(id={self.id}, title='{self.title}', type='{self.content_type}')>"

class LearningProgress(Base):
    __tablename__ = 'learning_progress'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    progress_percentage = Column(Float, default=0.0)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    is_completed = Column(Boolean, default=False)
    time_spent_seconds = Column(Integer, default=0) # For detailed analytics

    # Relationships
    user = relationship("User", back_populates="progress")
    course = relationship("Course", back_populates="learning_progress")

    __table_args__ = (
        Index('idx_learning_progress_user_id', 'user_id'),
        Index('idx_learning_progress_course_id', 'course_id'),
        Index('idx_learning_progress_user_course', 'user_id', 'course_id', unique=True), # Composite index for quick lookup
    )

    def __repr__(self):
        return f"<LearningProgress(user_id={self.user_id}, course_id={self.course_id}, progress={self.progress_percentage:.1f}%)>"

class Assessment(Base):
    __tablename__ = 'assessments'
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    title = Column(String, nullable=False)
    assessment_type = Column(String) # 'quiz', 'exam', 'assignment'
    max_score = Column(Integer)
    ai_graded = Column(Boolean, default=False) # Flag if ML powered grading is used

    # Relationships
    course = relationship("Course", back_populates="assessments")
    results = relationship("AssessmentResult", back_populates="assessment")

    __table_args__ = (
        Index('idx_assessment_course_id', 'course_id'),
    )

    def __repr__(self):
        return f"<Assessment(id={self.id}, title='{self.title}')>"

class AssessmentResult(Base):
    __tablename__ = 'assessment_results'
    id = Column(Integer, primary_key=True)
    assessment_id = Column(Integer, ForeignKey('assessments.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    score = Column(Float)
    submission_date = Column(DateTime, default=datetime.utcnow)
    feedback = Column(Text) # ML-generated feedback or instructor feedback

    # Relationships
    assessment = relationship("Assessment", back_populates="results")
    user = relationship("User") # No back_populates here to avoid circular ref if not needed

    __table_args__ = (
        Index('idx_assessment_result_assessment_id', 'assessment_id'),
        Index('idx_assessment_result_user_id', 'user_id'),
    )

    def __repr__(self):
        return f"<AssessmentResult(user_id={self.user_id}, assessment_id={self.assessment_id}, score={self.score})>"

class Interaction(Base):
    __tablename__ = 'interactions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content_id = Column(Integer, ForeignKey('content.id')) # Can be null if interaction is with course/platform
    interaction_type = Column(String, nullable=False) # 'view', 'like', 'comment', 'share', 'search'
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(Text) # JSON or text for specific interaction details (e.g., search query)

    # Relationships
    user = relationship("User", back_populates="interactions")
    content = relationship("Content", back_populates="interactions")

    __table_args__ = (
        Index('idx_interaction_user_id', 'user_id'),
        Index('idx_interaction_content_id', 'content_id'),
        Index('idx_interaction_type', 'interaction_type'),
    )

    def __repr__(self):
        return f"<Interaction(user_id={self.user_id}, type='{self.interaction_type}', timestamp='{self.timestamp}')>" 