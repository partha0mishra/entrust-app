from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter()

@router.post("/", response_model=schemas.User)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin)
):
    """
    Create a new user. (Admin only)
    """
    # Check if user_id already exists
    existing = db.query(models.User).filter(
        models.User.user_id == user.user_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="User ID already exists"
        )
    
    # Validate customer requirement for customer users
    if user.user_type in [models.UserType.CXO, models.UserType.PARTICIPANT]:
        if not user.customer_id:
            raise HTTPException(
                status_code=400, 
                detail="Customer users (CXO/Participant) must have a customer assigned"
            )
    
    # Hash password
    hashed_password = auth.get_password_hash(user.password)
    
    # Prepare user data
    user_dict = user.dict()
    del user_dict['password']
    
    # Create new user
    db_user = models.User(**user_dict, password_hash=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.get("/", response_model=List[schemas.UserWithCustomer])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin)
):
    """
    List all users (non-deleted) with customer information. (Admin only)
    """
    users = db.query(models.User).filter(
        models.User.is_deleted == False
    ).offset(skip).limit(limit).all()
    
    return users

@router.get("/{user_id}", response_model=schemas.UserWithCustomer)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin)
):
    """
    Get a specific user by ID with customer information. (Admin only)
    """
    user = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.is_deleted == False
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@router.put("/{user_id}", response_model=schemas.User)
def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin)
):
    """
    Update a user. (Admin only)
    Password is optional - if not provided, existing password is kept.
    """
    db_user = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.is_deleted == False
    ).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get update data (exclude unset fields)
    update_data = user_update.dict(exclude_unset=True)
    
    # Handle password update
    if 'password' in update_data and update_data['password']:
        update_data['password_hash'] = auth.get_password_hash(update_data['password'])
        del update_data['password']
    
    # Apply updates
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin)
):
    """
    Soft delete a user. (Admin only)
    Sets is_deleted flag to True instead of actually deleting.
    """
    db_user = db.query(models.User).filter(
        models.User.id == user_id
    ).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Soft delete
    db_user.is_deleted = True
    db.commit()
    
    return {"message": "User deleted successfully"}