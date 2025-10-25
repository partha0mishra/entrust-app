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
    existing = db.query(models.User).filter(
        models.User.user_id == user.user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User ID already exists")
    
    if user.user_type in [models.UserType.CXO, models.UserType.PARTICIPANT] and not user.customer_id:
        raise HTTPException(status_code=400, detail="Customer users must have a customer assigned")
    
    hashed_password = auth.get_password_hash(user.password)
    user_dict = user.dict()
    plain_password = user_dict['password']  # Store plain password
    del user_dict['password']
    
    db_user = models.User(
        **user_dict, 
        password_hash=hashed_password,
        password=plain_password  # Store plain text for admin viewing
    )
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
    db_user = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.is_deleted == False
    ).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_update.dict(exclude_unset=True)
    if 'password' in update_data and update_data['password']:
        plain_password = update_data['password']
        update_data['password_hash'] = auth.get_password_hash(plain_password)
        update_data['password'] = plain_password  # Store plain text too
    
    for key, value in update_data.items():
        if key != 'password':  # Don't set password field directly
            setattr(db_user, key, value)
    
    # Handle password separately
    if 'password' in update_data:
        db_user.password = update_data['password']
        db_user.password_hash = update_data['password_hash']
    
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin)
):
    db_user = db.query(models.User).filter(
        models.User.id == user_id
    ).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_user.is_deleted = True
    db.commit()
    return {"message": "User deleted successfully"}