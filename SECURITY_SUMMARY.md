# EnTrust Application - Security Analysis Summary

**Report Date**: 2025-11-13  
**Analyzed Version**: Latest (claude/agentic-survey-analysis-enhancement branch)

---

## Executive Summary

The EnTrust application has **5 CRITICAL security vulnerabilities** that require immediate remediation before production deployment:

| # | Severity | Issue | File | Impact |
|---|----------|-------|------|--------|
| 1 | **CRITICAL** | Credentials in URL parameters | Login.jsx:16 | Password exposure in logs, history, proxies |
| 2 | **CRITICAL** | Plain text passwords in DB | models.py:36, users.py:32 | All accounts compromised if DB breached |
| 3 | **CRITICAL** | Default admin creds in logs | main.py:38 | Trivial unauthorized access |
| 4 | **CRITICAL** | SSL/TLS verify=False | llm_providers.py:131 | MITM attack on AWS Bedrock |
| 5 | **CRITICAL** | Secrets in API responses | llm_config.py:80 | Cloud credentials exposed to frontend |
| 6 | **HIGH** | Missing input validation | models.py, survey.py | Invalid data injection attacks |
| 7 | **HIGH** | Missing authorization checks | customers.py:42, reports.py | Data leakage across tenants |
| 8 | **HIGH** | No rate limiting | all routers | Brute force & DOS attacks |
| 9 | **HIGH** | No account lockout | auth.py | Credential brute force |
| 10 | **MEDIUM** | Weak CORS config | main.py:93 | CSRF attacks if misconfigured |

---

## CRITICAL FINDINGS DETAIL

### 1. Login Credentials in URL Parameters (CRITICAL)

**Location**: `frontend/src/pages/Login.jsx` line 16

**Current Code**:
```javascript
const response = await fetch(`${API_URL}/api/auth/login?user_id=${userId}&password=${password}`, {
  method: 'POST',
});
```

**Vulnerability**: Passwords transmitted as URL query parameters instead of request body

**Exposure Routes**:
- Browser history (plaintext)
- Server access logs
- HTTP proxies and CDNs
- Browser cache
- Referrer headers
- Screenshots/screen shares

**Fix**: Move credentials to JSON body

```javascript
const response = await fetch(`${API_URL}/api/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ user_id: userId, password: password })
});
```

---

### 2. Plain Text Passwords Stored in Database (CRITICAL)

**Location**: `backend/app/models.py` line 36, `users.py` lines 32, 83

**Current Code**:
```python
class User(Base):
    password_hash = Column(String(255), nullable=False)  # Properly hashed
    password = Column(Text, nullable=True)  # PLAINTEXT! For admin viewing
```

**Impact**: Database breach = all user passwords compromised

**Violations**: GDPR, CCPA, PCI-DSS, HIPAA, SOC 2

**Fix**: Remove plaintext password field entirely
```python
class User(Base):
    id = Column(Integer, primary_key=True)
    password_hash = Column(String(255), nullable=False)
    # DELETE: password = Column(Text, nullable=True)
```

Implement proper password reset flow instead.

---

### 3. Default Admin Credentials Printed to Logs (CRITICAL)

**Location**: `backend/app/main.py` lines 37-38

**Current Code**:
```python
print("[INIT] [OK] Default admin user created!")
print("[INIT]    User ID: admin")
print("[INIT]    Password: Welcome123!")  # ← EXPOSED!
```

**Exposure**: Docker logs, Kubernetes logs, Syslog, any log aggregation system

**Fix**: Remove credential printing, implement forced password reset on first login

```python
print("[INIT] [OK] Default admin user created!")
print("[INIT] User ID: admin (password reset required on first login)")
# Don't print the password!
```

---

### 4. SSL/TLS Verification Disabled (CRITICAL)

**Location**: `backend/app/llm_providers.py` line 131

**Current Code**:
```python
self._client = boto3.client(
    'bedrock-runtime',
    region_name=self.region,
    aws_access_key_id=self.access_key_id,
    aws_secret_access_key=self.secret_access_key,
    config=config,
    verify=False  # ← CRITICAL VULNERABILITY
)
```

**Vulnerability**: Man-in-the-Middle (MITM) attacks possible

**Fix**: Remove verify=False (defaults to True)

```python
self._client = boto3.client(
    'bedrock-runtime',
    region_name=self.region,
    aws_access_key_id=self.access_key_id,
    aws_secret_access_key=self.secret_access_key,
    config=config
    # verify=True is default - omit the parameter
)
```

---

### 5. AWS/Azure Credentials Exposed in API Response (CRITICAL)

**Location**: `backend/app/routers/llm_config.py` line 80

**Current Code**:
```python
@router.get("/", response_model=List[schemas.LLMConfig])
def list_llm_configs(...):
    configs = db.query(models.LLMConfig).all()
    return configs  # Returns ALL fields including secrets!
```

**Data Exposed**:
```json
{
  "aws_access_key_id": "AKIA...",
  "aws_secret_access_key": "wJalr...",
  "azure_api_key": "key-...",
  "api_key": "..."
}
```

**Impact**: Cloud credentials compromised, accessible from browser dev tools

**Fix**: Create separate schema without secrets

```python
class LLMConfigSafe(BaseModel):
    id: int
    purpose: str
    provider_type: LLMProviderType
    model_name: str
    status: str
    # OMIT: aws_access_key_id, aws_secret_access_key, azure_api_key, api_key

@router.get("/", response_model=List[schemas.LLMConfigSafe])
def list_llm_configs(...):
    configs = db.query(models.LLMConfig).all()
    return [LLMConfigSafe.from_orm(c) for c in configs]
```

---

## HIGH SEVERITY FINDINGS

### 6. Missing Input Validation

**Affected Endpoints**: `/survey/responses`, `/customers`, `/users`

**Issues**:
- Score field is String, should be Integer(1-10)
- No max length validation on text fields
- No regex validation on customer codes
- Pagination limits not enforced

**Example Attack**:
```json
{
  "question_id": 1,
  "score": "INVALID_VALUE",
  "comment": "A" * 100000
}
```

**Fix**: Use Pydantic validation

```python
class SurveyResponseCreate(BaseModel):
    question_id: int
    score: int = Field(ge=1, le=10)
    comment: str = Field(max_length=200)
```

---

### 7. Missing Authorization Checks (Multi-Tenant Data Leakage)

**Location**: `backend/app/routers/customers.py` lines 42-52

**Current Code**:
```python
@router.get("/")
def list_customers(skip: int = 0, limit: int = 100, ...,
                  current_user = Depends(auth.get_current_user)):
    """Available to ALL authenticated users"""
    return db.query(models.Customer).filter(
        models.Customer.is_deleted == False
    ).all()  # Returns ALL customers!
```

**Issue**: CXO from Company A can see Company B's data

**Fix**: Implement tenant isolation

```python
@router.get("/")
def list_customers(..., current_user = Depends(auth.get_current_user)):
    if current_user.user_type == models.UserType.SYSTEM_ADMIN:
        # Admins see all
        return db.query(models.Customer).filter(...).all()
    elif current_user.user_type == models.UserType.CXO:
        # CXO only sees own customer
        if not current_user.customer_id:
            raise HTTPException(403)
        customer = db.query(models.Customer).filter(
            models.Customer.id == current_user.customer_id
        ).first()
        return [customer] if customer else []
    else:
        raise HTTPException(403)
```

---

### 8. No Rate Limiting

**Vulnerable Endpoints**:
- `/auth/login` - Brute force attacks
- `/survey/responses` - Spam submissions
- `/reports/customer/{id}/dimension/{dim}` - LLM API abuse
- `/llm-config/{id}/test` - Provider flooding

**Fix**: Add rate limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/minute")
def login(...):
    ...
```

---

### 9. No Account Lockout

**Vulnerability**: Unlimited failed login attempts possible

**Fix**: Implement lockout mechanism

```python
class User(Base):
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)

# In login endpoint:
if user.locked_until and user.locked_until > datetime.utcnow():
    raise HTTPException(403, "Account locked. Try again later.")

if not auth.verify_password(password, user.password_hash):
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= 5:
        user.locked_until = datetime.utcnow() + timedelta(minutes=15)
    db.commit()
    raise HTTPException(401)
```

---

## MEDIUM SEVERITY FINDINGS

### 10. Weak CORS Configuration

**Location**: `backend/app/main.py` lines 93-104

**Issue**: Allow all methods and headers, potentially vulnerable if ALLOWED_ORIGINS="*"

**Fix**:
```python
ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=600
)
```

---

### 11. Weak JWT Configuration

**Issues**:
- Default SECRET_KEY is weak
- Token expiry is 24 hours (too long)

**Fix**:
```python
# In .env or deployment
SECRET_KEY=<generate-256-bit-random-key>
ACCESS_TOKEN_EXPIRE_MINUTES=60  # 1 hour
```

---

### 12. JWT in localStorage (XSS Vulnerable)

**Location**: `frontend/src/pages/Login.jsx` lines 23-24

**Issue**: localStorage accessible to XSS attacks

**Fix**: Use httpOnly cookies

```python
# Backend sets cookie
response.headers['Set-Cookie'] = 'token=...;HttpOnly;Secure;SameSite=Strict'

# Frontend doesn't need localStorage
```

---

## DATA FLOW SUMMARY

### Survey Data Flow:
```
User Input → SQLAlchemy ORM → Database
                    ↓
        Aggregate Metrics (Safe - ORM prevents SQL injection)
                    ↓
        RAG Context Retrieval (ChromaDB vector search)
                    ↓
        LLM Prompt Injection (Data chunked, context injected)
                    ↓
        LLM Analysis (LOCAL/Bedrock/Azure)
                    ↓
        Report Generation (Markdown + JSON)
                    ↓
        File Storage (/app/entrust/reports/)
                    ↓
        PDF Download
```

### Key Security Properties:
✓ SQL Injection: Protected (ORM-based queries)
✓ User Isolation: Responses scoped to user_id
✓ Survey Isolation: Responses scoped to survey_id
✗ Tenant Isolation: MISSING (All CXOs see all customers)
✗ XSS Protection: WEAK (JWT in localStorage, plain password in response)
✗ Authentication: CRITICAL flaws (URL params, plaintext storage)

---

## REMEDIATION PRIORITY

### IMMEDIATE (Before ANY production use):
1. Fix login credentials in URL
2. Remove plaintext password field
3. Remove credential logging
4. Enable SSL/TLS verification
5. Stop exposing secrets in API responses

### WEEK 1:
6. Add input validation
7. Implement tenant isolation
8. Add rate limiting
9. Implement account lockout
10. Fix CORS configuration

### MONTH 1:
11. Implement proper JWT handling (httpOnly cookies)
12. Add audit logging
13. Implement password reset flow
14. Add monitoring/alerting
15. Security review of LLM integrations

### ONGOING:
- Regular security audits
- Penetration testing
- Dependency updates
- Log monitoring

---

## ADDITIONAL OBSERVATIONS

### Positive Security Practices:
- Using SQLAlchemy ORM (prevents SQL injection)
- JWT-based authentication (stateless)
- Password hashing with bcrypt
- Soft deletes (is_deleted flag)
- Role-based access control structure

### Areas of Concern:
- No encryption at rest
- No audit logging
- No secrets management (env vars only)
- RAG context shared across all customers (privacy concern)
- No API rate limiting
- Minimal error handling

---

## COMPLIANCE IMPACTS

**Current Violations**:
- **GDPR**: Plaintext password storage, no audit logs
- **CCPA**: Customer data accessible across tenants
- **PCI-DSS**: Weak password handling, no rate limiting
- **HIPAA**: No audit trail for health data access
- **SOC 2**: No access controls, insufficient logging

**Cannot be production-ready until CRITICAL issues are fixed.**

---

**Full Analysis**: See `/home/user/entrust_app_security_analysis.md`
