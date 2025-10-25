from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
from . import models, schemas
from .database import get_db
import os
import base64

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# For password hashing (login verification)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# For password encryption (viewing passwords)
# Generate a key from SECRET_KEY for Fernet
ENCRYPTION_KEY = base64.urlsafe_b64encode(SECRET_KEY.encode().ljust(32)[:32])
cipher_suite = Fernet(ENCRYPTION_KEY)

security = HTTPBearer()

def verify_password(plain_password, hashed_password):
    # Truncate to 72 bytes for bcrypt compatibility
    truncated_password = plain_password[:72] if len(plain_password) > 72 else plain_password
    return pwd_context.verify(truncated_password, hashed_password)

def get_password_hash(password):
    # Truncate to 72 bytes for bcrypt compatibility
    truncated_password = password[:72] if len(password) > 72 else password
    return pwd_context.hash(truncated_password)

def encrypt_password(password: str) -> str:
    """Encrypt password so it can be viewed later"""
    return cipher_suite.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password: str) -> str:
    """Decrypt password for viewing"""
    try:
        return cipher_suite.decrypt(encrypted_password.encode()).decode()
    except Exception:
        return "****"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
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
):
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
    
    user = db.query(models.User).filter(
        models.User.user_id == user_id,
        models.User.is_deleted == False
    ).first()
    
    if user is None:
        raise credentials_exception
    return user

def require_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.user_type != models.UserType.SYSTEM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def require_customer_user(current_user: models.User = Depends(get_current_user)):
    if current_user.user_type not in [models.UserType.CXO, models.UserType.PARTICIPANT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customer users can access surveys"
        )
    return current_user

def require_report_access(current_user: models.User = Depends(get_current_user)):
    """CXO and Sales users can access reports"""
    if current_user.user_type not in [models.UserType.CXO, models.UserType.SALES]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only CXO and Sales users can access reports"
        )
    return current_user