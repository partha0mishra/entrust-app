from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base, SessionLocal
from .routers import auth_router, customers, users, llm_config, survey, reports
from . import models, auth
import json
import os

# Create database tables
Base.metadata.create_all(bind=engine)

# Default credentials that can be overridden via environment variables
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "Welcome123!")
DEFAULT_SAMPLE_PASSWORD = os.getenv("DEFAULT_SAMPLE_PASSWORD", "Welcome123!")


def ensure_default_admin(db):
    """Create or refresh the default system admin account."""
    admin_user = db.query(models.User).filter(
        models.User.user_id == "admin"
    ).first()

    if not admin_user:
        print("\n[INIT] Creating default admin user...")
        admin_user = models.User(
            user_id="admin",
            username="System Administrator",
            password_hash=auth.get_password_hash(DEFAULT_ADMIN_PASSWORD),
            password=auth.encrypt_password(DEFAULT_ADMIN_PASSWORD),
            user_type=models.UserType.SYSTEM_ADMIN,
            customer_id=None
        )
        db.add(admin_user)
    else:
        print("\n[INIT] Admin user already exists. Updating password for consistency.")
        admin_user.password_hash = auth.get_password_hash(DEFAULT_ADMIN_PASSWORD)
        admin_user.password = auth.encrypt_password(DEFAULT_ADMIN_PASSWORD)
        admin_user.is_deleted = False

    db.commit()
    print("[INIT]    User ID: admin")
    print(f"[INIT]    Password: {DEFAULT_ADMIN_PASSWORD}")


def ensure_questions_loaded(db):
    """Load survey questions the first time the API runs."""
    question_count = db.query(models.Question).count()
    if question_count > 0:
        print(f"[INIT] Questions already loaded ({question_count} entries).")
        return

    questions_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions.json')
    if not os.path.exists(questions_file):
        print(f"[INIT] [WARNING] questions.json not found at {questions_file}")
        return

    print("[INIT] Loading questions from questions.json...")
    try:
        with open(questions_file, 'r', encoding='utf-8') as f:
            questions_data = json.load(f)

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
    except Exception as exc:
        print(f"[INIT] [WARNING] Could not load questions: {exc}")
        db.rollback()


def ensure_sample_customer(db):
    """Seed a demo customer and users so the UI is not empty on first launch."""
    existing_customers = db.query(models.Customer).filter(models.Customer.is_deleted == False).count()
    if existing_customers > 0:
        print(f"[INIT] Customers already present ({existing_customers}). Skipping sample data.")
        return

    print("[INIT] Creating sample EVTech customer data...")
    customer = models.Customer(
        customer_code="EVTC",
        name="EVTech Inc",
        industry="Automotive & Energy",
        location="Austin, Texas",
        description="Sample automotive customer seeded automatically for demos"
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    sample_specs = [
        ("ewhite", "Ethan White", models.UserType.CXO, customer.id),
        ("mthomas", "Maria Thomas", models.UserType.PARTICIPANT, customer.id),
        ("pjohnson", "Paul Johnson", models.UserType.PARTICIPANT, customer.id),
        ("Nagaraj", "Nagaraj", models.UserType.SALES, None),
    ]

    for user_id, username, user_type, customer_id in sample_specs:
        user = db.query(models.User).filter(models.User.user_id == user_id).first()
        if not user:
            user = models.User(
                user_id=user_id,
                username=username,
                user_type=user_type,
                customer_id=customer_id,
            )
            db.add(user)

        user.customer_id = customer_id
        user.password_hash = auth.get_password_hash(DEFAULT_SAMPLE_PASSWORD)
        user.password = auth.encrypt_password(DEFAULT_SAMPLE_PASSWORD)
        user.is_deleted = False

    db.commit()
    print("[INIT] Sample EVTech customer and demo users created.")


# Initialize database with default admin user, questions, and sample data
def initialize_database():
    """Initialize the database with defaults on first startup."""
    db = SessionLocal()

    try:
        ensure_default_admin(db)
        ensure_questions_loaded(db)
        ensure_sample_customer(db)
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

# Simple middleware to honor Azure's forwarded HTTPS headers
class ForwardedProtoMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            forwarded_proto = None
            for name, value in scope.get("headers", []):
                if name == b"x-forwarded-proto":
                    forwarded_proto = value.decode("latin-1").split(",")[0].strip()
                    break

            if forwarded_proto:
                scope = dict(scope)
                scope["scheme"] = forwarded_proto

        await self.app(scope, receive, send)

# Configure CORS - support both ALLOWED_ORIGINS and legacy CORS_ORIGINS env vars
cors_origin_env = (
    os.getenv("ALLOWED_ORIGINS")
    or os.getenv("CORS_ORIGINS")
    or "http://localhost:3000"
)
# Normalize by splitting on comma and stripping whitespace/empty values
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in cors_origin_env.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure FastAPI respects Azure Container Apps' forwarded HTTPS headers
app.add_middleware(ForwardedProtoMiddleware)

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