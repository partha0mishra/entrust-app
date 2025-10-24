from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import auth_router, customers, users, llm_config, survey, reports

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="EnTrust API",
    description="Data Governance Survey Platform API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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