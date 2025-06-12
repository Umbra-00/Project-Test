# Copyright (c) 2024 Umbra. All rights reserved.
from pydantic import BaseModel, HttpUrl, ConfigDict
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str # Password for creation, not stored directly

class User(UserBase):
    id: int
    role: str
    registration_date: datetime
    last_login: Optional[datetime] = None
    learning_preferences: Optional[str] = None # JSON or similar for structured preferences

    model_config = ConfigDict(from_attributes=True)

class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    url: HttpUrl

class CourseCreate(CourseBase):
    pass

class Course(CourseBase):
    id: int
    created_by_user_id: Optional[int] = None
    creation_date: datetime
    difficulty_level: Optional[str] = None
    ai_generated_version: int

    model_config = ConfigDict(from_attributes=True) 