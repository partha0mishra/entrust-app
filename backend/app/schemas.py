from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from .models import UserType, LLMProviderType

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
    
    model_config = ConfigDict(from_attributes=True)

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
    password: Optional[str] = None  # For returning decrypted password to admin
    
    model_config = ConfigDict(from_attributes=True)

class UserWithCustomer(User):
    customer: Optional[Customer] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class LLMConfigBase(BaseModel):
    purpose: str
    provider_type: LLMProviderType = LLMProviderType.LOCAL
    model_name: Optional[str] = "default"

    # Local LLM fields
    api_url: Optional[str] = None
    api_key: Optional[str] = None

    # AWS Bedrock fields
    aws_region: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_model_id: Optional[str] = None

    # Azure OpenAI fields
    azure_endpoint: Optional[str] = None
    azure_api_key: Optional[str] = None
    azure_deployment_name: Optional[str] = None
    azure_api_version: Optional[str] = "2024-02-15-preview"

class LLMConfigCreate(LLMConfigBase):
    pass

class LLMConfigUpdate(LLMConfigBase):
    pass

class LLMConfig(LLMConfigBase):
    id: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class QuestionBase(BaseModel):
    question_id: int
    text: str
    category: Optional[str]
    dimension: str
    question_type: Optional[str]
    guidance: Optional[str]
    process: Optional[str]
    lifecycle_stage: Optional[str]

class Question(QuestionBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

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
    
    model_config = ConfigDict(from_attributes=True)

class Survey(BaseModel):
    id: int
    customer_id: int
    status: str
    submitted_at: Optional[datetime]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class DimensionProgress(BaseModel):
    dimension: str
    total_questions: int
    answered_questions: int
    status: str
    categories: List[str] = []
    processes: List[str] = []
    lifecycle_stages: List[str] = []