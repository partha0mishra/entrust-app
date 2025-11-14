#!/usr/bin/env python3
"""
Script to delete all survey data, responses, and users (except admin)
"""
from app.database import SessionLocal
from app import models

def delete_all_data():
    """Delete all survey data, responses, and users (except admin)"""
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("  DELETING ALL DATA (EXCEPT ADMIN)")
        print("=" * 70)
        
        # Delete in order to respect foreign key constraints
        
        # 1. Delete survey responses
        print("\n[1/5] Deleting survey responses...")
        responses_count = db.query(models.SurveyResponse).count()
        db.query(models.SurveyResponse).delete()
        db.commit()
        print(f"✓ Deleted {responses_count} survey responses")
        
        # 2. Delete user survey submissions
        print("\n[2/5] Deleting user survey submissions...")
        submissions_count = db.query(models.UserSurveySubmission).count()
        db.query(models.UserSurveySubmission).delete()
        db.commit()
        print(f"✓ Deleted {submissions_count} user survey submissions")
        
        # 3. Delete surveys
        print("\n[3/5] Deleting surveys...")
        surveys_count = db.query(models.Survey).count()
        db.query(models.Survey).delete()
        db.commit()
        print(f"✓ Deleted {surveys_count} surveys")
        
        # 4. Delete users (except admin)
        print("\n[4/5] Deleting users (except admin)...")
        users_count = db.query(models.User).filter(
            models.User.user_id != "admin"
        ).count()
        db.query(models.User).filter(
            models.User.user_id != "admin"
        ).delete()
        db.commit()
        print(f"✓ Deleted {users_count} users (admin preserved)")
        
        # 5. Delete customers
        print("\n[5/5] Deleting customers...")
        customers_count = db.query(models.Customer).count()
        db.query(models.Customer).delete()
        db.commit()
        print(f"✓ Deleted {customers_count} customers")
        
        print("\n" + "=" * 70)
        print("  DATA DELETION COMPLETE")
        print("=" * 70)
        print("✓ All data deleted successfully (admin user preserved)")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    delete_all_data()

