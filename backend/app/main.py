from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base, SessionLocal
from .routers import auth_router, customers, users, llm_config, survey, reports
from . import models, auth
import json
import os

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize database with default admin user and questions
def initialize_database():
    """Initialize the database with default admin user and questions on first startup."""
    db = SessionLocal()
    
    try:
        # Create default admin user if it doesn't exist
        admin_user = db.query(models.User).filter(
            models.User.user_id == "admin"
        ).first()
        
        if not admin_user:
            print("\n[INIT] Creating default admin user...")
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
            print("[INIT] [OK] Default admin user created!")
            print("[INIT]    User ID: admin")
            print("[INIT]    Password: Welcome123!")
        else:
            print("[INIT] Admin user already exists, skipping creation.")
        
        # Load questions from JSON file if database is empty
        question_count = db.query(models.Question).count()
        if question_count == 0:
            questions_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions.json')
            if os.path.exists(questions_file):
                print("[INIT] Loading questions from questions.json...")
                try:
                    with open(questions_file, 'r', encoding='utf-8') as f:
                        questions_data = json.load(f)
                    
                    print(f"[INIT] Found {len(questions_data)} questions in file.")
                    
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
                    print(f"[INIT] [OK] Loaded {len(questions_data)} questions into database!")
                except Exception as e:
                    print(f"[INIT] [WARNING] Could not load questions: {e}")
            else:
                print(f"[INIT] [WARNING] questions.json not found at {questions_file}")
        else:
            print(f"[INIT] Questions already loaded ({question_count} questions), skipping.")
            
    except Exception as e:
        print(f"[INIT] [WARNING] Database initialization had issues: {e}")
        db.rollback()
    finally:
        db.close()

# Run initialization on startup
initialize_database()

# Initialize FastAPI app
app = FastAPI(
    title="EnTrust API",
    description="Data Governance Survey Platform API",
    version="1.0.0"
)

# Configure CORS - allow origins from environment or default to localhost
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS", 
    "http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])
app.include_router(customers.router, prefix="/api/customers", tags=["customers"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(llm_config.router, prefix="/api/llm-config", tags=["llm-config"])
app.include_router(survey.router, prefix="/api/survey", tags=["survey"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])

@app.get("/")
def read_root():
    """Root endpoint - API health check"""
    return {
        "message": "EnTrust API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "healthy"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}