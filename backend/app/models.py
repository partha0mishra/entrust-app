from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
import enum

class UserType(str, enum.Enum):
    SYSTEM_ADMIN = "SystemAdmin"
    CXO = "CXO"
    PARTICIPANT = "Participant"
    SALES = "Sales"

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_code = Column(String(50), unique=True, index=True)
    name = Column(String(255), nullable=False)
    industry = Column(String(255))
    location = Column(String(255))
    description = Column(Text)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    users = relationship("User", back_populates="customer")
    surveys = relationship("Survey", back_populates="customer")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, index=True)
    username = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    password = Column(Text, nullable=True)  # NEW LINE - Plain text for viewing
    user_type = Column(SQLEnum(UserType), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    customer = relationship("Customer", back_populates="users")
    survey_responses = relationship("SurveyResponse", back_populates="user")

# ... rest of the models remain the same (LLMConfig, Question, Survey, SurveyResponse)

class LLMProviderType(str, enum.Enum):
    LOCAL = "LOCAL"
    BEDROCK = "BEDROCK"
    AZURE = "AZURE"

class LLMConfig(Base):
    __tablename__ = "llm_configs"

    id = Column(Integer, primary_key=True, index=True)
    purpose = Column(String(100), unique=True, nullable=False)
    provider_type = Column(SQLEnum(LLMProviderType), nullable=False, default=LLMProviderType.LOCAL)

    # Common fields
    model_name = Column(String(100), default="default")
    status = Column(String(50), default="Not Tested")

    # Local LLM fields
    api_url = Column(String(500))  # For local LLMs (LM Studio, etc.)
    api_key = Column(String(500))  # Optional for local

    # AWS Bedrock fields
    aws_region = Column(String(50))  # e.g., "us-east-1"
    aws_access_key_id = Column(String(500))
    aws_secret_access_key = Column(String(500))
    aws_model_id = Column(String(200))  # e.g., "anthropic.claude-v2"
    aws_thinking_mode = Column(String(20))  # For Claude Sonnet: enabled, disabled (default: enabled)

    # Azure OpenAI fields
    azure_endpoint = Column(String(500))  # Azure endpoint URL
    azure_api_key = Column(String(500))
    azure_deployment_name = Column(String(200))  # Azure deployment name
    azure_api_version = Column(String(50), default="2024-02-15-preview")
    azure_reasoning_effort = Column(String(20))  # For GPT-5: minimal, low, medium, high

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, unique=True, nullable=False)
    text = Column(Text, nullable=False)
    category = Column(String(100))
    dimension = Column(String(255), nullable=False)
    question_type = Column(String(50))
    guidance = Column(Text)
    process = Column(String(100))
    lifecycle_stage = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

class Survey(Base):
    __tablename__ = "surveys"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(String(50), default="Not Started")
    submitted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="surveys")
    responses = relationship("SurveyResponse", back_populates="survey")

class UserSurveySubmission(Base):
    __tablename__ = "user_survey_submissions"

    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Ensure one submission per user per survey
    __table_args__ = (
        UniqueConstraint('survey_id', 'user_id', name='uq_survey_user'),
    )

class SurveyResponse(Base):
    __tablename__ = "survey_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    score = Column(String(10))
    comment = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    survey = relationship("Survey", back_populates="responses")
    user = relationship("User", back_populates="survey_responses")
    question = relationship("Question")