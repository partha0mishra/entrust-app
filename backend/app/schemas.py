from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .models import UserType

# Customer Schemas
class CustomerBase(BaseModel):
    name: str
    customer_code: str
    industry: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: int
    is_deleted: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# User Schemas
class UserBase(BaseModel):
    user_id: str
    username: str
    user_type: UserType
    customer_id: Optional[int] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    user_type: Optional[UserType] = None
    customer_id: Optional[int] = None
    password: Optional[str] = None

class User(UserBase):
    id: int
    is_deleted: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserWithCustomer(User):
    customer: Optional[Customer] = None

# Authentication Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

# LLM Config Schemas
class LLMConfigBase(BaseModel):
    purpose: str
    api_url: str
    api_key: Optional[str] = "None"
    model_name: Optional[str] = "default"  # NEW FIELD

class LLMConfigCreate(LLMConfigBase):
    pass

class LLMConfigUpdate(LLMConfigBase):
    pass

class LLMConfig(LLMConfigBase):
    id: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Question Schemas
class QuestionBase(BaseModel):
    question_id: int
    text: str
    category: Optional[str]
    dimension: str
    question_type: Optional[str]
    guidance: Optional[str]

class Question(QuestionBase):
    id: int
    
    class Config:
        from_attributes = True

# Survey Response Schemas
class SurveyResponseCreate(BaseModel):
    question_id: int
    score: Optional[str] = None
    comment: Optional[str] = None

class SurveyResponseUpdate(BaseModel):
    score: Optional[str] = None
    comment: Optional[str] = None

class SurveyResponse(BaseModel):
    id: int
    survey_id: int
    user_id: int
    question_id: int
    score: Optional[str]
    comment: Optional[str]
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Survey Schemas
class Survey(BaseModel):
    id: int
    customer_id: int
    status: str
    submitted_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Progress Tracking Schema
class DimensionProgress(BaseModel):
    dimension: str
    total_questions: int
    answered_questions: int
    status: str