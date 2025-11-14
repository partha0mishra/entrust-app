#!/usr/bin/env python3
"""Reset admin password to admin123"""
import sys
sys.path.insert(0, "/app")
from app.database import SessionLocal
from app import models, auth

db = SessionLocal()
try:
    admin_user = db.query(models.User).filter(models.User.user_id == "admin").first()
    if admin_user:
        new_password = "admin123"
        admin_user.password_hash = auth.get_password_hash(new_password)
        admin_user.password = auth.encrypt_password(new_password)
        db.commit()
        print(f"✓ Admin password reset to: {new_password}")
    else:
        print("✗ Admin user not found")
finally:
    db.close()

