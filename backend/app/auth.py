from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from . import models, schemas
from .database import get_db
import os

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token authentication
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a plain password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Dependency to get the current authenticated user.
    Validates JWT token and returns the user object.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    user = db.query(models.User).filter(
        models.User.user_id == user_id,
        models.User.is_deleted == False
    ).first()
    
    if user is None:
        raise credentials_exception
    
    return user

def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    """
    Dependency to require SystemAdmin role.
    Returns user if they are admin, otherwise raises 403.
    """
    if current_user.user_type != models.UserType.SYSTEM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. SystemAdmin role required."
        )
    return current_user

def require_customer_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    """
    Dependency to require customer user (CXO or Participant).
    Returns user if they are customer user, otherwise raises 403.
    """
    if current_user.user_type not in [models.UserType.CXO, models.UserType.PARTICIPANT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customer users (CXO or Participant) can access surveys"
        )
    return current_user

def require_report_access(current_user: models.User = Depends(get_current_user)) -> models.User:
    """
    Dependency to require report access (CXO or Sales).
    Returns user if they can view reports, otherwise raises 403.
    """
    if current_user.user_type not in [models.UserType.CXO, models.UserType.SALES]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only CXO and Sales users can access reports"
        )
    return current_user