"""
Script to reset the admin password
Usage: python reset_admin_password.py
"""

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models, auth

def reset_admin_password():
    """Reset admin password to 'Welcome123!'"""

    db = SessionLocal()

    try:
        # Find the admin user
        admin_user = db.query(models.User).filter(
            models.User.user_id == "admin"
        ).first()

        if not admin_user:
            print("❌ Admin user not found!")
            print("   Creating admin user...")
            admin_user = models.User(
                user_id="admin",
                username="System Administrator",
                user_type=models.UserType.SYSTEM_ADMIN,
                customer_id=None
            )
            db.add(admin_user)

        # Set new password
        new_password = "Welcome123!"
        admin_user.password_hash = auth.get_password_hash(new_password)
        admin_user.password = auth.encrypt_password(new_password)  # For viewing in admin UI

        db.commit()

        print("✅ Admin password has been reset successfully!")
        print("\n🔑 Login credentials:")
        print("   User ID: admin")
        print("   Password: Welcome123!")
        print("\n🚀 You can now login at http://localhost:3000")

    except Exception as e:
        print(f"\n❌ Error resetting password: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🔐 Resetting admin password...\n")
    reset_admin_password()
