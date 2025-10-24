from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter()

@router.post("/", response_model=schemas.Customer)
def create_customer(
    customer: schemas.CustomerCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin)
):
    """
    Create a new customer. (Admin only)
    """
    # Check if customer code already exists
    existing = db.query(models.Customer).filter(
        models.Customer.customer_code == customer.customer_code
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Customer code already exists"
        )
    
    # Create new customer
    db_customer = models.Customer(**customer.dict())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    
    return db_customer

@router.get("/", response_model=List[schemas.Customer])
def list_customers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    List all customers (non-deleted).
    Available to all authenticated users.
    """
    customers = db.query(models.Customer).filter(
        models.Customer.is_deleted == False
    ).offset(skip).limit(limit).all()
    
    return customers

@router.get("/{customer_id}", response_model=schemas.Customer)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Get a specific customer by ID.
    Available to all authenticated users.
    """
    customer = db.query(models.Customer).filter(
        models.Customer.id == customer_id,
        models.Customer.is_deleted == False
    ).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return customer

@router.put("/{customer_id}", response_model=schemas.Customer)
def update_customer(
    customer_id: int,
    customer_update: schemas.CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin)
):
    """
    Update a customer. (Admin only)
    Note: Customer ID cannot be updated.
    """
    db_customer = db.query(models.Customer).filter(
        models.Customer.id == customer_id,
        models.Customer.is_deleted == False
    ).first()
    
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Update fields
    for key, value in customer_update.dict().items():
        setattr(db_customer, key, value)
    
    db.commit()
    db.refresh(db_customer)
    
    return db_customer

@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin)
):
    """
    Soft delete a customer. (Admin only)
    Sets is_deleted flag to True instead of actually deleting.
    """
    db_customer = db.query(models.Customer).filter(
        models.Customer.id == customer_id
    ).first()
    
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Soft delete
    db_customer.is_deleted = True
    db.commit()
    
    return {"message": "Customer deleted successfully"}