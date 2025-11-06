import json
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models, auth

def init_database():
    """Initialize the database with tables, default admin user, and questions."""
    
    # Create all tables
    print("Creating database tables...")
    models.Base.metadata.create_all(bind=engine)
    print("[OK] Tables created successfully!")
    
    db = SessionLocal()
    
    try:
        # Create default admin user if it doesn't exist
        admin_user = db.query(models.User).filter(
            models.User.user_id == "admin"
        ).first()
        
        if not admin_user:
            print("\nCreating default admin user...")
            default_password = "Welcome123!"
            admin_user = models.User(
                user_id="admin",
                username="System Administrator",
                password_hash=auth.get_password_hash(default_password),
                password=auth.encrypt_password(default_password),  # For viewing in admin UI
                user_type=models.UserType.SYSTEM_ADMIN,
                customer_id=None
            )
            db.add(admin_user)
            db.commit()
            print("[OK] Default admin user created!")
            print("   User ID: admin")
            print("   Password: Welcome123!")
        else:
            print("\n[INFO] Admin user already exists, skipping creation.")
        
        # Load questions from JSON file
        question_count = db.query(models.Question).count()
        if question_count == 0:
            print("\nLoading questions from questions.json...")
            try:
                with open('questions.json', 'r', encoding='utf-8') as f:
                    questions_data = json.load(f)
                
                print(f"Found {len(questions_data)} questions in file.")
                
                for q in questions_data:
                    question = models.Question(
                        question_id=q['id'],
                        text=q['text'],
                        category=q.get('category'),
                        dimension=q['dimension'],
                        question_type=q.get('question_type'),
                        guidance=q.get('guidance'),
                        process=q.get('process'),
                        lifecycle_stage=q.get('lifecycle_stage')
                    )
                    db.add(question)
                
                db.commit()
                print(f"[OK] Loaded {len(questions_data)} questions into database!")
                
                # Show dimension summary
                dimensions = db.query(models.Question.dimension).distinct().all()
                print(f"\nQuestions loaded across {len(dimensions)} dimensions:")
                for dim in dimensions:
                    count = db.query(models.Question).filter(
                        models.Question.dimension == dim[0]
                    ).count()
                    print(f"   - {dim[0]}: {count} questions")
                    
            except FileNotFoundError:
                print("[ERROR] questions.json file not found!")
                print("   Please place questions.json in the backend directory.")
            except json.JSONDecodeError as e:
                print(f"[ERROR] Invalid JSON in questions.json: {e}")
        else:
            print(f"\n[INFO] Questions already loaded ({question_count} questions), skipping.")
        
        print("\n" + "="*50)
        print("[OK] Database initialization complete!")
        print("="*50)
        print("\nSummary:")
        print(f"   - Tables: Created")
        print(f"   - Admin User: {'Created' if not admin_user else 'Already exists'}")
        print(f"   - Questions: {db.query(models.Question).count()} loaded")
        print(f"   - Customers: {db.query(models.Customer).count()}")
        print(f"   - Users: {db.query(models.User).count()}")
        print("\nYou can now start using the application!")
        print("   Frontend: http://localhost:3000")
        print("   Backend API: http://localhost:8000")
        print("   API Docs: http://localhost:8000/docs")
        print("\nLogin credentials:")
        print("   User ID: admin")
        print("   Password: Welcome123!")
        print()
        
    except Exception as e:
        print(f"\n[ERROR] Error initializing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_database()