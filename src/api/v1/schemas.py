# Copyright (c) 2024 Umbra. All rights reserved.
from pydantic import BaseModel, HttpUrl, ConfigDict, Field
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    user_identifier: str # This will be the user-provided unique ID

class UserCreate(UserBase):
    password: str = Field(min_length=4) # Password for creation, with min length of 4

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
    instructor: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    difficulty_level: Optional[str] = None # Aligned with database model
    category: Optional[str] = None
    platform: Optional[str] = None

class CourseCreate(CourseBase):
    pass

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
    user_identifier: Optional[str] = None # Renamed from username 