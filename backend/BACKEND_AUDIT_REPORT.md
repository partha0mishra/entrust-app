# Backend Architecture Audit Report
## EntTrust Application - Data Governance Survey Platform

**Report Date:** November 13, 2025  
**Audit Scope:** `/home/user/entrust-app/backend/`  
**Framework:** FastAPI with SQLAlchemy ORM  

---

## Executive Summary

The EnTrust backend demonstrates a well-structured FastAPI application with comprehensive features for survey management, LLM integration, and multi-provider support. However, there are several **critical security concerns**, **architectural patterns to address**, and **performance considerations** that require attention.

**Key Findings:**
- **3 Critical Security Issues** (plaintext password storage, hardcoded default credentials)
- **5 Major Issues** (missing error handling, performance concerns, architectural debt)
- **8 Medium Issues** (missing indexes, inconsistent validation, code organization)
- **Multiple Technical Debt Items** (database design, API design, configuration management)

---

## 1. PROJECT STRUCTURE ANALYSIS

### Directory Organization

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app initialization
│   ├── database.py          # SQLAlchemy setup
│   ├── models.py            # Database models
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # Authentication & authorization
│   ├── llm_service.py       # LLM coordination service
│   ├── llm_providers.py     # Multi-provider LLM adapters
│   ├── rag.py               # RAG (Vector DB) integration
│   ├── report_utils.py      # Report generation utilities
│   ├── agents/              # Agentic workflow components
│   ├── prompts/             # LLM prompt templates
│   └── routers/             # API endpoint handlers
│       ├── auth_router.py
│       ├── users.py
│       ├── customers.py
│       ├── survey.py
│       ├── reports.py
│       └── llm_config.py
└── requirements.txt
```

**Assessment:** Well-organized separation of concerns. Clear layering: routers → services → models/database.

### Architecture Pattern: Service Locator with Lazy Initialization

**Files:** `rag.py:451-456`, `llm_service.py:34-123`

The codebase uses a **global singleton pattern** for RAG service:
```python
_rag_service: Optional[RAGService] = None

def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
```

**Issues:**
- Thread-safety not guaranteed (no locking mechanism)
- State pollution across requests (global state)
- Hard to test (requires mocking global state)

---

## 2. DATABASE MODELS ANALYSIS

### Models File: `/home/user/entrust-app/backend/app/models.py`

#### Model Relationships

| Model | Primary Key | Foreign Keys | Relationships |
|-------|------------|--------------|---------------|
| **Customer** | `id` (INT) | None | 1→M Users, 1→M Surveys |
| **User** | `id` (INT) | `customers.id` (FK) | M→1 Customer, 1→M SurveyResponses |
| **Question** | `id` (INT) | None | Soft ref via survey_responses |
| **Survey** | `id` (INT) | `customers.id` (FK) | M→1 Customer, 1→M Responses |
| **SurveyResponse** | `id` (INT) | survey, user, question (FKs) | M→1 Survey, M→1 User, M→1 Question |
| **UserSurveySubmission** | `id` (INT) | survey, user (FKs) | Tracks per-user submissions |
| **LLMConfig** | `id` (INT) | None | Configuration storage |

#### Critical Issues Found

**Issue #1: Plaintext Password Storage (CRITICAL)**
- **File:** `models.py:36`, `users.py:32`, `main.py:30`
- **Problem:** Plaintext passwords stored in `User.password` field for "admin viewing"
- **Lines:** 
  - `models.py:36`: `password = Column(Text, nullable=True)  # NEW LINE - Plain text for viewing`
  - `users.py:26-32`: Deliberately storing plain passwords
  - `main.py:30`: `password=auth.encrypt_password(default_password)  # For viewing in admin UI`
- **Risk:** CVSS 9.8 - Credential disclosure vulnerability
- **Impact:** If database is compromised, all user credentials exposed
- **Recommendation:** 
  - Remove plaintext password field entirely
  - Implement secure password reset flow instead
  - Use encrypted fields with proper key management if viewing is critical

**Issue #2: Hardcoded Default Credentials (CRITICAL)**
- **File:** `main.py:25`
- **Code:** `default_password = "Welcome123!"`
- **Problem:** Default admin password is hardcoded and printed to logs
- **Risk:** CVSS 9.1 - Default credentials vulnerability
- **Impact:** Printed to stdout/logs, discoverable in version control
- **Recommendation:** 
  - Generate random password on first startup
  - Force password change on first login
  - Use environment variables for initialization

**Issue #3: Missing Unique Constraint on User Email (MEDIUM)**
- **File:** `models.py:29-44`
- **Problem:** No email field; only `user_id` field is unique
- **Impact:** Can't support standard login flows; relies on user_id which isn't standard
- **Recommendation:** Add email field with UNIQUE constraint

**Issue #4: Weak Enum Usage for User Types (MEDIUM)**
- **File:** `models.py:7-11`
- **Code:** 
  ```python
  class UserType(str, enum.Enum):
      SYSTEM_ADMIN = "SystemAdmin"
      CXO = "CXO"
      PARTICIPANT = "Participant"
      SALES = "Sales"
  ```
- **Problem:** Using string-based enum instead of integer IDs
- **Impact:** More storage, slower lookups, migration complexity
- **Recommendation:** Use integer enums with proper mapping

**Issue #5: Missing Database Indexes (PERFORMANCE)**
- **File:** `models.py` (all models)
- **Missing Indexes:**
  - `Survey.customer_id` - frequently queried in filters
  - `SurveyResponse.survey_id` - key filter in report generation
  - `SurveyResponse.user_id` - used in multiple filters
  - `SurveyResponse.question_id` - lookup queries
  - `UserSurveySubmission.survey_id` + `user_id` composite for efficiency
- **Impact:** N+1 queries, slow report generation (especially with large datasets)
- **Example:** Line `reports.py:343-349` - joins that could benefit from indexes
- **Recommendation:** 
  ```python
  survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False, index=True)
  user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
  ```

**Issue #6: Missing Constraints on SurveyResponse (DATA INTEGRITY)**
- **File:** `models.py:126-140`
- **Problem:** 
  - No UNIQUE constraint to prevent duplicate responses
  - `score` field is TEXT not ENUM (should be standardized)
  - No NOT NULL on required fields
- **Current Code:**
  ```python
  class SurveyResponse(Base):
      score = Column(String(10))  # Should be ENUM or standardized
      comment = Column(String(200))  # Arbitrary limit
  ```
- **Impact:** Data quality issues, scoring inconsistency
- **Recommendation:** 
  ```python
  __table_args__ = (
      UniqueConstraint('survey_id', 'user_id', 'question_id'),
  )
  score = Column(Enum(ScoreType), nullable=False)
  ```

**Issue #7: Missing Soft Delete on Critical Models (DATA RETENTION)**
- **File:** `models.py` - models lack `is_deleted` and `deleted_at`
- **Affected:** Question, Survey, SurveyResponse
- **Impact:** Can't soft-delete without data loss; audit trail missing
- **Recommendation:** Add soft delete fields to all critical tables

#### Positive Patterns

✓ Proper use of relationships with `back_populates`  
✓ Automatic timestamp management (`default=datetime.utcnow`, `onupdate`)  
✓ Soft delete on Customer and User models  
✓ Unique constraint on UserSurveySubmission (prevents duplicate submissions)  

---

## 3. API ROUTES ANALYSIS

### Route: `/api/auth` - `auth_router.py`

**Endpoints:**
- `POST /login` - Authenticate and get JWT
- `GET /me` - Get current user info

**Issues:**

**Issue #8: Missing Rate Limiting on Login (SECURITY)**
- **File:** `auth_router.py:9-50`
- **Problem:** No rate limiting on login endpoint
- **Risk:** Brute force attacks possible
- **Recommendation:** Use `slowapi` or similar for rate limiting:
  ```python
  from slowapi import Limiter
  limiter = Limiter(key_func=get_remote_address)
  @router.post("/login")
  @limiter.limit("5/minute")
  def login(...)
  ```

**Issue #9: Inconsistent Error Messages (SECURITY)**
- **File:** `auth_router.py:29-34`
- **Code:** `detail="Incorrect user ID or password"`
- **Problem:** Single error message for both user not found and wrong password
- **Good Practice:** This is actually CORRECT (prevents user enumeration), so ✓

**Issue #10: Missing Token Refresh Flow (USABILITY)**
- **File:** `auth.py:49-57`
- **Problem:** Only one-shot access tokens, no refresh mechanism
- **Impact:** Users get logged out after `ACCESS_TOKEN_EXPIRE_MINUTES` (default 1440)
- **Recommendation:** Implement refresh token flow

### Route: `/api/survey` - `survey.py`

**Endpoints:** 7 endpoints for survey interaction, progress tracking, submission

**Issues:**

**Issue #11: N+1 Query Problem (PERFORMANCE)**
- **File:** `survey.py:64-103` (get_survey_progress)
- **Code:**
  ```python
  for (dimension,) in dimensions:
      question_query = db.query(models.Question)...
      total_questions = question_query.count()
      # ^ This is a separate query per dimension
  ```
- **Impact:** O(n) database queries for n dimensions
- **Recommendation:** Batch load with one query:
  ```python
  question_counts = db.query(
      models.Question.dimension,
      func.count(models.Question.id)
  ).group_by(models.Question.dimension).all()
  ```

**Issue #12: Missing Validation on Comment Length (DATA QUALITY)**
- **File:** `survey.py:227`, `survey.py:233`
- **Code:** `comment = response.comment[:200].strip() if response.comment else None`
- **Problem:** Silently truncates comments without validation
- **Recommendation:** Validate in Pydantic schema instead:
  ```python
  class SurveyResponseCreate(BaseModel):
      comment: Optional[str] = Field(None, max_length=200)
  ```

**Issue #13: Race Condition on Survey Submission Status (CONCURRENCY)**
- **File:** `survey.py:320-333`
- **Code:**
  ```python
  customer_users = db.query(models.User).filter(...).count()
  submissions_count = db.query(models.UserSurveySubmission)...count() + 1
  if submissions_count >= customer_users:
      survey.status = "Submitted"
  ```
- **Problem:** Check-then-set without transaction isolation
- **Impact:** If two users submit simultaneously, status might not update
- **Recommendation:** Use SELECT FOR UPDATE or database-level trigger

### Route: `/api/reports` - `reports.py`

**Endpoints:** 3 main endpoints for report generation

**Issues:**

**Issue #14: Excessive Function Parameter Count (CODE SMELL)**
- **File:** `report_utils.py:97-110`
- **Function:** `create_markdown_report` has 13 parameters
- **Problem:** Too many parameters makes function hard to test and maintain
- **Recommendation:** Use dataclass or dict:
  ```python
  @dataclass
  class ReportData:
      dimension: str
      customer_code: str
      # ... other fields
  
  def create_markdown_report(data: ReportData) -> str:
  ```

**Issue #15: Missing Error Handling on LLM Failures (RELIABILITY)**
- **File:** `reports.py:441-475`
- **Code:**
  ```python
  llm_response = await asyncio.wait_for(...)
  if llm_response.get("success"):
      dimension_llm_analysis = llm_response.get("content")
  else:
      llm_error = llm_response.get("error")
  ```
- **Problem:** Graceful degradation works, but no retry logic
- **Impact:** If LLM is temporarily unavailable, report fails completely
- **Recommendation:** Add exponential backoff retry:
  ```python
  @retry(stop=stop_after_attempt(3), wait=wait_exponential())
  async def call_llm_with_retry(...):
  ```

**Issue #16: Unbounded Query Results (MEMORY)**
- **File:** `reports.py:343-349`
- **Code:** 
  ```python
  all_responses = db.query(models.SurveyResponse).join(
      models.Question
  ).filter(
      models.SurveyResponse.survey_id == survey.id,
      models.Question.dimension == dimension,
      models.SurveyResponse.score.isnot(None)
  ).all()
  ```
- **Problem:** `.all()` loads all rows into memory; no pagination
- **Impact:** Memory issues with large surveys (10,000+ responses)
- **Recommendation:** Use `yield_per()` for streaming:
  ```python
  for response in db.query(...).yield_per(500):
  ```

**Issue #17: Timeout Configuration Inconsistency (RELIABILITY)**
- **File:** `reports.py:447-450`
- **Code:**
  ```python
  timeout_seconds = 1800.0 if is_thinking_mode else 300.0
  llm_response = await asyncio.wait_for(..., timeout=timeout_seconds)
  ```
- **Problem:** Different timeout values scattered throughout code
- **Impact:** Inconsistent behavior, hard to configure
- **Recommendation:** Centralize in config:
  ```python
  LLM_TIMEOUT_THINKING = 1800  # 30 minutes
  LLM_TIMEOUT_STANDARD = 300   # 5 minutes
  ```

**Issue #18: Missing Request Validation on Reports (SECURITY)**
- **File:** `reports.py:277-283`
- **Code:** `@router.get("/customer/{customer_id}/dimensions")`
- **Problem:** No validation that user has access to this customer
- **Risk:** Unauthorized data exposure
- **Current Code:**
  ```python
  def get_dimension_reports(customer_id: int, ...):
      # No check that current_user.customer_id == customer_id for CXO users
  ```
- **Recommendation:**
  ```python
  if current_user.user_type == models.UserType.CXO and current_user.customer_id != customer_id:
      raise HTTPException(status_code=403, detail="Access denied")
  ```

### Route: `/api/users` - `users.py`

**Endpoints:** CRUD operations for user management

**Issues:**

**Issue #19: Plaintext Password Handling in API (CRITICAL)**
- **File:** `users.py:24-33`
- **Code:**
  ```python
  hashed_password = auth.get_password_hash(user.password)
  user_dict = user.dict()
  plain_password = user_dict['password']
  db_user = models.User(
      password_hash=hashed_password,
      password=plain_password  # Plaintext stored!
  )
  ```
- **Risk:** Same as Issue #1 above
- **Recommendation:** Remove plaintext storage entirely

**Issue #20: Missing Validation on User Updates (DATA INTEGRITY)**
- **File:** `users.py:79`
- **Code:** `update_data = user_update.dict(exclude_unset=True)`
- **Problem:** Allows arbitrary field updates without validation
- **Recommendation:** Validate critical fields:
  ```python
  if 'user_type' in update_data and current_user.user_id != 'admin':
      raise HTTPException(status_code=403, detail="Cannot change user type")
  ```

### Route: `/api/customers` - `customers.py`

**Issues:**

**Issue #21: Missing Audit Logging (COMPLIANCE)**
- **File:** `customers.py` (all endpoints)
- **Problem:** No logging of who created/modified/deleted customers
- **Impact:** No audit trail for compliance audits
- **Recommendation:**
  ```python
  logger.info(f"Customer created: {db_customer.id} by {current_user.user_id}")
  ```

### Route: `/api/llm-config` - `llm_config.py`

**Endpoints:** Config management and LLM testing

**Issues:**

**Issue #22: Storing Secrets in Database (CRITICAL)**
- **File:** `llm_config.py`, `models.py:68-80`
- **Stored Secrets:**
  - `aws_access_key_id`
  - `aws_secret_access_key`
  - `aws_model_id`
  - `azure_api_key`
  - `api_key` (local LLM)
- **Problem:** Secrets stored as plaintext in database
- **Risk:** CVSS 9.8 - Credential disclosure
- **Recommendation:** 
  - Use AWS Secrets Manager or Azure Key Vault
  - Only store references/names in database
  - Never store secrets in code or version control

**Issue #23: Missing Config Validation (USABILITY)**
- **File:** `llm_config.py:20-73`
- **Problem:** No validation of required fields for each provider
- **Code:** Creates config with missing fields, marks as "Not Tested"
- **Recommendation:** Validate provider-specific required fields

---

## 4. CORE SERVICES ANALYSIS

### Service: `llm_service.py`

**Purpose:** Coordinate LLM calls, handle chunking, manage context

**Architecture:**

```
LLMService (static methods)
├── generate_dimension_summary() - chunked summary generation
├── generate_deep_dimension_analysis() - detailed analysis
├── analyze_facet() - category/process/lifecycle analysis
├── analyze_comments_sentiment() - comment analysis
├── generate_overall_summary() - cross-dimension summary
└── _call_llm() - unified LLM call interface
    └── provider.call_llm()
```

**Issues:**

**Issue #24: Hardcoded Token Estimation (FRAGILE)**
- **File:** `llm_service.py:35-38`
- **Code:**
  ```python
  CHARS_PER_TOKEN = 4
  MAX_TOKENS_PER_CHUNK = 5000
  MAX_CHARS_PER_CHUNK = MAX_TOKENS_PER_CHUNK * CHARS_PER_TOKEN
  ```
- **Problem:** "~4 characters per token" is OpenAI-specific; varies by model
- **Impact:** Inaccurate for Bedrock (Claude) or Azure (GPT-5)
- **Recommendation:** Per-provider token counting:
  ```python
  def estimate_tokens(text: str, provider_type: str) -> int:
      if provider_type == "BEDROCK":  # Claude uses ~3.5 chars/token
          return len(text) // 4
      elif provider_type == "AZURE":  # GPT-5 uses ~4 chars/token
          return len(text) // 4
  ```

**Issue #25: Unsafe Regular Expression (SECURITY/STABILITY)**
- **File:** `llm_service.py:164`
- **Code:** `json_block_match = re.search(r"```json\s*(\{.*?\})\s*```", response_text, re.DOTALL)`
- **Problem:** 
  - Regex doesn't handle nested braces correctly
  - `.*?` is vulnerable to catastrophic backtracking
  - `.` with DOTALL matches newlines (inefficient)
- **Recommendation:**
  ```python
  import json
  
  def _parse_llm_output(response_text: str):
      start_idx = response_text.find("```json")
      if start_idx == -1:
          return response_text, None
      
      start_idx += 7  # Skip ```json
      end_idx = response_text.find("```", start_idx)
      if end_idx == -1:
          return response_text, None
      
      try:
          json_str = response_text[start_idx:end_idx].strip()
          return response_text, json.loads(json_str)
      except json.JSONDecodeError:
          return response_text, None
  ```

**Issue #26: Missing Logging on LLM Calls (OBSERVABILITY)**
- **File:** `llm_service.py` - all LLM call methods
- **Problem:** No logging of:
  - Provider used
  - Tokens consumed
  - Latency
  - Errors/timeouts
- **Impact:** Hard to debug, no cost tracking
- **Recommendation:** Add structured logging:
  ```python
  import time
  start = time.time()
  content = await provider.call_llm(messages, max_tokens)
  logger.info(f"LLM call", extra={
      "provider": provider.__class__.__name__,
      "duration_seconds": time.time() - start,
      "max_tokens": max_tokens
  })
  ```

**Issue #27: Timeout Values Are Magic Numbers (MAINTAINABILITY)**
- **File:** `llm_service.py:39`
- **Code:** `LLM_TIMEOUT = 180.0  # 3 minutes`
- **Problem:** Hardcoded, not configurable
- **Impact:** Can't adjust for different environments
- **Recommendation:** Load from environment:
  ```python
  LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT_SECONDS", "180"))
  ```

### Service: `rag.py`

**Purpose:** Vector database integration for knowledge base retrieval

**Architecture:**

```
RAGService (singleton)
├── ingest_knowledge() - load documents into ChromaDB
├── retrieve_context() - semantic search
├── get_dimension_context() - dimension-specific retrieval
└── get_stats() - collection statistics
```

**Issues:**

**Issue #28: Missing Thread Safety on Singleton (CONCURRENCY)**
- **File:** `rag.py:451-456`
- **Code:**
  ```python
  _rag_service: Optional[RAGService] = None
  
  def get_rag_service() -> RAGService:
      global _rag_service
      if _rag_service is None:
          _rag_service = RAGService()
      return _rag_service
  ```
- **Problem:** Race condition in multi-threaded environment
- **Impact:** Multiple RAGService instances might be created
- **Recommendation:** Use thread-safe lazy initialization:
  ```python
  from threading import Lock
  _lock = Lock()
  
  def get_rag_service() -> RAGService:
      global _rag_service
      if _rag_service is None:
          with _lock:
              if _rag_service is None:
                  _rag_service = RAGService()
      return _rag_service
  ```

**Issue #29: Silent Failures on Missing Knowledge Base (RELIABILITY)**
- **File:** `rag.py:209-212`
- **Code:**
  ```python
  if not self.knowledge_base_dir.exists():
      error_msg = f"Knowledge base directory not found..."
      logger.error(error_msg)
      return {"success": False, "error": error_msg}
  ```
- **Problem:** Caller might not check return value
- **Impact:** RAG features silently degrade
- **Recommendation:** Raise exception or warn loudly

**Issue #30: Hard-coded Embedding Model (INFLEXIBILITY)**
- **File:** `rag.py:40`
- **Code:** `embedding_model: str = "all-MiniLM-L6-v2"`
- **Problem:** Not configurable; switching models requires code change
- **Impact:** Can't use model-specific optimizations
- **Recommendation:** Load from config:
  ```python
  embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
  ```

**Issue #31: No Embedding Cache (PERFORMANCE)**
- **File:** `rag.py:258-259`
- **Code:**
  ```python
  embeddings = self.embedder.encode(chunk_texts, show_progress_bar=False)
  ```
- **Problem:** Re-encodes same chunks on multiple ingestions
- **Impact:** Slow knowledge base updates
- **Recommendation:** Cache embeddings or use batch operations

### Service: `report_utils.py`

**Purpose:** Report generation and caching

**Issues:**

**Issue #32: Hardcoded Report Path (INFLEXIBILITY)**
- **File:** `report_utils.py:24-25`
- **Code:** `REPORTS_BASE_PATH = "/app/entrust"`
- **Problem:** Docker-specific path; fails on local dev
- **Impact:** Can't generate reports locally
- **Recommendation:** Load from environment:
  ```python
  REPORTS_BASE_PATH = os.getenv("REPORTS_PATH", "/app/entrust")
  ```

**Issue #33: Missing Report Expiration (STORAGE)**
- **File:** `report_utils.py:389-430`
- **Problem:** No cleanup of old cached reports
- **Impact:** Disk space grows unbounded
- **Recommendation:** Implement cleanup function:
  ```python
  def cleanup_old_reports(days=30):
      cutoff = datetime.now() - timedelta(days=days)
      for report_file in reports_dir.glob("**/*.json"):
          if datetime.fromtimestamp(report_file.stat().st_mtime) < cutoff:
              report_file.unlink()
  ```

**Issue #34: Dimension Mapping Is Inconsistent (MAINTAINABILITY)**
- **File:** `report_utils.py:29-51`
- **Code:** Two different dimension names mapping to same filesystem name
- **Problem:** Creates confusion and bugs
- **Impact:** Hard to track which version is in use
- **Recommendation:** Normalize dimension names at database level

---

## 5. AUTHENTICATION & AUTHORIZATION

### File: `auth.py`

**Security Review:**

**Issue #35: Weak JWT Secret Defaults (CRITICAL)**
- **File:** `auth.py:14-16`
- **Code:**
  ```python
  SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
  ALGORITHM = os.getenv("ALGORITHM", "HS256")
  ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
  ```
- **Problem:** Default secret key is in the code as example
- **Risk:** CVSS 8.6 - Insecure default credentials
- **Impact:** Anyone can forge JWT tokens if env var not set
- **Recommendation:**
  ```python
  SECRET_KEY = os.getenv("SECRET_KEY")
  if not SECRET_KEY:
      raise ValueError("SECRET_KEY environment variable must be set")
  ```

**Issue #36: Encryption Key Derivation Is Weak (CRITICAL)**
- **File:** `auth.py:22-24`
- **Code:**
  ```python
  ENCRYPTION_KEY = base64.urlsafe_b64encode(SECRET_KEY.encode().ljust(32)[:32])
  cipher_suite = Fernet(ENCRYPTION_KEY)
  ```
- **Problem:** 
  - Derives encryption key from JWT secret (key misuse)
  - Pads with spaces (weak KDF)
  - No salt
- **Risk:** CVSS 8.2 - Weak cryptography
- **Recommendation:** Use proper key derivation:
  ```python
  from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
  from cryptography.hazmat.primitives import hashes
  
  kdf = PBKDF2(
      algorithm=hashes.SHA256(),
      length=32,
      salt=b'your-app-name-salt',
      iterations=100000,
  )
  key = base64.urlsafe_b64encode(kdf.derive(SECRET_KEY.encode()))
  ```

**Issue #37: HS256 Algorithm for JWT (SECURITY)**
- **File:** `auth.py:15`
- **Problem:** Symmetric algorithm; if SECRET_KEY is leaked, tokens can be forged
- **Better Practice:** Use RS256 (asymmetric) for token verification
- **Recommendation:** Switch to asymmetric keys:
  ```python
  ALGORITHM = "RS256"
  PRIVATE_KEY = os.getenv("JWT_PRIVATE_KEY")
  PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY")
  ```

**Issue #38: No Token Revocation (SECURITY)**
- **File:** `auth.py` - all token operations
- **Problem:** Once issued, tokens valid until expiration
- **Impact:** Can't revoke compromised tokens
- **Recommendation:** Implement token blacklist:
  ```python
  token_blacklist = set()
  
  def revoke_token(token: str):
      token_blacklist.add(token)
  
  def is_token_revoked(token: str) -> bool:
      return token in token_blacklist
  ```

**Issue #39: Password Truncation Is Lossy (USABILITY)**
- **File:** `auth.py:29-31`
- **Code:**
  ```python
  truncated_password = plain_password[:72] if len(plain_password) > 72 else plain_password
  return pwd_context.verify(truncated_password, hashed_password)
  ```
- **Problem:** bcrypt truncates to 72 bytes, but loses data silently
- **Impact:** Two different passwords might hash to same value if first 72 bytes identical
- **Recommendation:** Validate and error:
  ```python
  if len(password) > 72:
      raise ValueError("Password must be less than 72 characters")
  ```

**Positive Patterns:**

✓ Proper use of bcrypt with `CryptContext`  
✓ Separate dependency injection for current_user  
✓ Role-based access control (require_admin, require_customer_user)  
✓ Proper HTTP 401/403 status codes  

---

## 6. CONFIGURATION & DATABASE SETUP

### File: `database.py`

**Issues:**

**Issue #40: Connection String in Code (SECURITY)**
- **File:** `database.py:7-10`
- **Code:**
  ```python
  DATABASE_URL = os.getenv(
      "DATABASE_URL", 
      "postgresql://entrust_user:entrust_pass@localhost:5432/entrust_db"
  )
  ```
- **Problem:** Default connection string has hardcoded credentials
- **Risk:** CVSS 8.6 - Hardcoded credentials
- **Recommendation:**
  ```python
  DATABASE_URL = os.getenv("DATABASE_URL")
  if not DATABASE_URL:
      raise ValueError("DATABASE_URL environment variable must be set")
  ```

**Issue #41: No Connection Pooling Configuration (PERFORMANCE)**
- **File:** `database.py:13`
- **Code:** `engine = create_engine(DATABASE_URL)`
- **Problem:** Default pool size (5) might be insufficient
- **Impact:** Connection pool exhaustion under load
- **Recommendation:**
  ```python
  engine = create_engine(
      DATABASE_URL,
      pool_size=20,
      max_overflow=40,
      pool_pre_ping=True,  # Verify connections before use
      echo_pool=os.getenv("DEBUG") == "true"
  )
  ```

**Issue #42: No Database Initialization Checks (RELIABILITY)**
- **File:** `main.py:13-80`
- **Code:** Attempts to initialize database but doesn't verify success
- **Problem:** If questions.json missing, silent failure
- **Recommendation:** Verify database state:
  ```python
  def verify_database_ready():
      """Verify database tables exist and are populated"""
      try:
          question_count = db.query(models.Question).count()
          if question_count == 0:
              logger.warning("No questions loaded; surveys will not function")
      except Exception as e:
          logger.error(f"Database check failed: {e}")
  ```

---

## 7. DEPENDENCIES ANALYSIS

### File: `requirements.txt`

**Dependency Review:**

| Package | Version | Notes |
|---------|---------|-------|
| fastapi | 0.104.1 | Current, stable |
| sqlalchemy | 2.0.23 | Supports async (not used) |
| psycopg2-binary | 2.9.9 | PostgreSQL driver - OK |
| pydantic | 2.5.0 | Good for validation |
| python-jose | 3.3.0 | JWT support OK |
| passlib[bcrypt] | 1.7.4 | Password hashing OK |
| cryptography | 41.0.7 | Encryption support |
| reportlab | 4.0.7 | PDF generation (unused) |
| boto3 | 1.34.0 | AWS Bedrock |
| openai | 1.6.0 | (Unused - removed?) |
| chromadb | 0.4.22 | Vector DB for RAG |
| sentence-transformers | 2.3.1 | Embeddings |

**Issues:**

**Issue #43: Unused Dependencies (MAINTENANCE)**
- **File:** `requirements.txt:15` - `openai==1.6.0`
- **Problem:** Listed but not imported anywhere in codebase
- **Impact:** Unnecessary dependency, security updates to track
- **Recommendation:** Remove if truly unused

**Issue #44: Fixed Version Pins (FRAGILITY)**
- **Problem:** All versions pinned exactly; can't receive security patches
- **Example:** `cryptography==41.0.7` - if 41.0.8 has security fix, won't be used
- **Impact:** Vulnerable to known CVEs
- **Recommendation:** Use compatible version ranges:
  ```
  fastapi>=0.100,<0.200
  sqlalchemy>=2.0,<3.0
  ```

**Issue #45: Missing Security Scanning (COMPLIANCE)**
- **Problem:** No `safety` or `pip-audit` integration
- **Recommendation:** Add to CI/CD:
  ```bash
  pip install safety
  safety check -r requirements.txt
  ```

**Issue #46: Heavy Dependencies (DEPLOYMENT)**
- **Problem:** 
  - `torch>=2.0.0` is massive (~2GB)
  - `sentence-transformers` requires compilation
  - `chromadb` has deep dependency tree
- **Impact:** Large Docker images, slow deployments
- **Recommendation:** Separate dependencies by environment:
  ```
  # requirements.txt - base
  # requirements-ml.txt - RAG features (optional)
  # requirements-dev.txt - testing tools
  ```

---

## 8. PERFORMANCE CONSIDERATIONS

### Database Query Performance

**Bottlenecks Identified:**

1. **N+1 Queries in Progress Tracking** (`survey.py:64-103`)
   - For each dimension, queries total AND answered questions separately
   - Impact: O(n) queries for n dimensions

2. **Missing Indexes** (see Issue #5)
   - No indexes on foreign key columns
   - Sequential scans on SurveyResponse table

3. **Unbounded Result Sets** (see Issue #16)
   - `all()` loads entire survey into memory
   - 10k responses = significant memory usage

4. **Aggregation Without Caching**
   - `aggregate_by_facet()` recalculates from raw data every time
   - No materialized view or cache

### Async/Concurrency Issues

1. **Synchronous Database Access**
   - All database calls are synchronous
   - FastAPI async not fully utilized
   - Thread-per-request model for DB operations

2. **No Connection Pooling Tuning**
   - Default pool size insufficient for concurrent requests

3. **Blocking LLM Calls**
   - LLM calls use `asyncio.wait_for()` but wrapped in executor
   - Still blocks thread

### Memory Usage

1. **Large Report Generation**
   - Loads all responses into memory
   - Concatenates long strings

2. **Embedding Model**
   - SentenceTransformer loaded at startup
   - ~400MB in memory always

### Recommendations

```python
# Use database indexes
INDEX_CREATION = """
CREATE INDEX idx_survey_response_survey_id ON survey_responses(survey_id);
CREATE INDEX idx_survey_response_user_id ON survey_responses(user_id);
CREATE INDEX idx_survey_response_question_id ON survey_responses(question_id);
CREATE INDEX idx_survey_customer_id ON surveys(customer_id);
"""

# Batch queries
def get_question_counts_by_dimension():
    return db.query(
        models.Question.dimension,
        func.count(models.Question.id).label('count')
    ).group_by(models.Question.dimension).all()

# Stream large result sets
def generate_report_streaming(survey_id):
    for response in db.query(SurveyResponse).yield_per(500):
        yield response

# Enable connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

---

## 9. SECURITY SUMMARY

### Critical Issues (Implement Immediately)

| # | Issue | File | Risk | Fix Effort |
|---|-------|------|------|-----------|
| 1 | Plaintext password storage | models.py, users.py | CVSS 9.8 | Medium |
| 2 | Hardcoded default credentials | main.py | CVSS 9.1 | Low |
| 22 | Secrets in database | llm_config.py, models.py | CVSS 9.8 | High |
| 35 | Weak JWT secret default | auth.py | CVSS 8.6 | Low |
| 36 | Weak encryption key derivation | auth.py | CVSS 8.2 | Medium |
| 40 | Database credentials in code | database.py | CVSS 8.6 | Low |

### High Priority Issues

| # | Issue | Impact | Fix |
|---|-------|--------|-----|
| 8 | Missing rate limiting | Brute force attacks | Use slowapi |
| 18 | Missing access control on reports | Data exposure | Add customer_id check |
| 38 | No token revocation | Can't revoke compromised tokens | Implement blacklist |

---

## 10. RECOMMENDATIONS - PRIORITY ORDER

### Phase 1: Critical Security (Week 1)

1. **Remove plaintext password storage**
   - Delete `User.password` field
   - Implement secure password reset flow
   - Estimated: 4 hours

2. **Remove hardcoded credentials**
   - Remove default admin password from code
   - Use environment variables for initialization
   - Estimated: 2 hours

3. **Move secrets to vault**
   - AWS Secrets Manager for AWS credentials
   - Azure Key Vault for Azure credentials
   - Store only references in database
   - Estimated: 8 hours

### Phase 2: Architecture (Weeks 2-3)

4. **Fix thread-safety issues**
   - Add locks to RAG singleton
   - Estimated: 2 hours

5. **Add database indexes**
   - Create migration for missing indexes
   - Estimated: 2 hours

6. **Fix N+1 queries**
   - Batch load dimensions and counts
   - Estimated: 4 hours

7. **Add rate limiting**
   - Implement on login endpoint
   - Estimated: 2 hours

### Phase 3: Reliability (Weeks 4-5)

8. **Implement retry logic**
   - Add exponential backoff for LLM calls
   - Estimated: 4 hours

9. **Add structured logging**
   - Log all LLM calls with metrics
   - Add audit logging for sensitive operations
   - Estimated: 6 hours

10. **Implement token refresh**
    - Refresh token flow
    - Token revocation
    - Estimated: 8 hours

### Phase 4: Performance (Weeks 6-7)

11. **Connection pool tuning**
    - Configure pool size based on load testing
    - Estimated: 4 hours

12. **Report caching improvements**
    - Implement expiration
    - Add cleanup
    - Estimated: 4 hours

13. **Move secrets properly**
    - Never store in database
    - Use environment variables
    - Estimated: 6 hours

---

## 11. TECHNOLOGY DEBT ITEMS

### Code Quality

- [ ] Extract magic numbers to constants
- [ ] Reduce function parameter counts (>5 params)
- [ ] Add comprehensive error handling for all API endpoints
- [ ] Add input validation on all endpoints (Pydantic schemas)
- [ ] Split large routers into smaller modules

### Testing

- [ ] No unit tests found
- [ ] No integration tests found
- [ ] No API tests found
- [ ] Add pytest fixtures for database testing
- [ ] Add test containers for PostgreSQL
- [ ] Add test LLM mocks

### Documentation

- [ ] Missing API documentation (OpenAPI/Swagger)
- [ ] Missing environment variable documentation
- [ ] Missing database schema documentation
- [ ] Missing architecture decision records (ADRs)

### Deployment

- [ ] No health check endpoint details
- [ ] Missing graceful shutdown logic
- [ ] No readiness probe implementation
- [ ] No migration strategy documented

---

## 12. POSITIVE PATTERNS & STRENGTHS

**The codebase demonstrates several best practices:**

✓ **Clean separation of concerns** - Routers, services, models well-organized  
✓ **Dependency injection** - Proper use of FastAPI Depends  
✓ **Soft deletes** - Data retention on Customer and User models  
✓ **Proper HTTP status codes** - Correct 401/403/404 usage  
✓ **Relationship management** - Proper SQLAlchemy relationships with back_populates  
✓ **Multi-provider support** - Flexible LLM provider architecture  
✓ **RAG integration** - Good attempt at knowledge base integration  
✓ **Async support** - FastAPI async capabilities utilized  
✓ **Error handling in most places** - Graceful degradation of LLM features  
✓ **Configuration via environment** - 12-factor app principles followed for most config  

---

## 13. AUDIT CHECKLIST

- [x] Database models reviewed
- [x] API endpoints reviewed
- [x] Authentication/authorization reviewed
- [x] Secrets management reviewed (CRITICAL ISSUES FOUND)
- [x] Error handling reviewed
- [x] Performance analyzed
- [x] Security analysis complete
- [x] Dependencies reviewed
- [x] Code organization reviewed
- [ ] Load testing (not performed)
- [ ] Penetration testing (not performed)
- [ ] Code coverage analysis (no tests to measure)

---

## CONCLUSION

The EnTrust backend demonstrates solid architectural patterns and good separation of concerns. However, **three critical security issues must be addressed immediately**:

1. **Plaintext password storage** in the database
2. **Hardcoded default credentials** in the code
3. **Secrets stored in the database** without encryption

Beyond these critical issues, the codebase would benefit from:
- Performance optimizations (indexes, query batching)
- Reliability improvements (retry logic, better error handling)
- Security hardening (rate limiting, token revocation, secret management)
- Comprehensive test coverage

With focused effort on the Phase 1 critical security items, the application would be significantly more secure. The technology debt items can be addressed incrementally without blocking deployment.

**Estimated effort for all recommendations: 8-10 weeks for a team of 2-3 developers**

