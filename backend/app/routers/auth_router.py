from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter()

@router.post("/login", response_model=schemas.Token)
def login(user_id: str, password: str, db: Session = Depends(get_db)):
    """
    Login endpoint - authenticates user and returns JWT token.
    
    Args:
        user_id: User's unique ID
        password: User's password
        db: Database session
    
    Returns:
        JWT access token and user information
    """
    # Find user by user_id
    user = db.query(models.User).filter(
        models.User.user_id == user_id,
        models.User.is_deleted == False
    ).first()
    
    # Verify user exists and password is correct
    if not user or not auth.verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect user ID or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.user_id}, 
        expires_delta=access_token_expires
    )
    
    # Convert user to schema
    user_schema = schemas.User.from_orm(user)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_schema
    }

@router.get("/me", response_model=schemas.UserWithCustomer)
def get_current_user_info(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user (from JWT token)
        db: Database session
    
    Returns:
        User information with customer details
    """
    user = db.query(models.User).filter(
        models.User.id == current_user.id
    ).first()
    
    return user