# EnTrust Security - Remediation Checklist

## CRITICAL ISSUES (Fix BEFORE ANY production deployment)

### Issue #1: Login Credentials in URL Parameters
- **File**: `/home/user/entrust-app/frontend/src/pages/Login.jsx`
- **Line**: 16
- **Status**: [ ] FIXED
- **What to do**:
  - Move credentials from URL parameters to JSON request body
  - Update backend auth router to accept JSON instead of query params
  - Add test case to verify credentials are NOT in URL

### Issue #2: Plain Text Passwords in Database
- **Files**: 
  - `/home/user/entrust-app/backend/app/models.py` line 36
  - `/home/user/entrust-app/backend/app/routers/users.py` lines 32, 83, 92
  - `/home/user/entrust-app/backend/app/auth.py` line 30
- **Status**: [ ] FIXED
- **What to do**:
  - Remove `password = Column(Text, nullable=True)` from User model
  - Remove `password=plain_password` from user creation/update
  - Remove `decrypt_password()` function if not needed
  - Update login response to NOT include password
  - Create migration script to clear existing plaintext passwords

### Issue #3: Default Admin Credentials in Logs
- **File**: `/home/user/entrust-app/backend/app/main.py`
- **Lines**: 37-38
- **Status**: [ ] FIXED
- **What to do**:
  - Remove print statement with password
  - Remove print statement with user_id (optional)
  - Implement initial login redirect forcing password reset
  - OR generate random password and send via secure channel

### Issue #4: SSL/TLS Verification Disabled (Bedrock)
- **File**: `/home/user/entrust-app/backend/app/llm_providers.py`
- **Line**: 131
- **Status**: [ ] FIXED
- **What to do**:
  - Remove `verify=False` parameter from boto3.client()
  - Test with verify=True to ensure it works
  - If cert issues occur, use proper CA bundle: `verify='/path/to/ca-bundle.crt'`

### Issue #5: Secrets Exposed in API Response
- **File**: `/home/user/entrust-app/backend/app/routers/llm_config.py`
- **Lines**: 75-81
- **Status**: [ ] FIXED
- **What to do**:
  - Create new Pydantic schema `LLMConfigSafe` without secret fields
  - Update response_model to use `LLMConfigSafe`
  - Update list endpoint to filter/map to safe schema
  - Verify GET response doesn't contain: aws_access_key_id, aws_secret_access_key, azure_api_key, api_key

---

## HIGH SEVERITY ISSUES (Fix within 1 week)

### Issue #6: Missing Input Validation
- **Files**:
  - `/home/user/entrust-app/backend/app/models.py` (SurveyResponse.score is String)
  - `/home/user/entrust-app/backend/app/schemas.py`
  - `/home/user/entrust-app/backend/app/routers/survey.py`
- **Status**: [ ] FIXED
- **What to do**:
  - Add Pydantic Field validators to schemas
  - Use `score: int = Field(ge=1, le=10)`
  - Add `comment: str = Field(max_length=200)`
  - Add pagination limits: `limit: int = Query(100, ge=1, le=100)`
  - Add customer_code validation (regex)

### Issue #7: Missing Authorization Checks (Tenant Isolation)
- **Files**:
  - `/home/user/entrust-app/backend/app/routers/customers.py` lines 37-72
  - `/home/user/entrust-app/backend/app/routers/reports.py`
- **Status**: [ ] FIXED
- **What to do**:
  - Add customer_id checks in all endpoints
  - CXO should only see own customer
  - PARTICIPANT should only see own customer
  - SALES should only see authorized customers
  - Admin can see all
  - Create authorization helper function

### Issue #8: No Rate Limiting
- **Files**: All routers
- **Status**: [ ] FIXED
- **What to do**:
  - Install slowapi: `pip install slowapi`
  - Create rate limiter in main.py
  - Add @limiter.limit() decorators to:
    - /auth/login: "5/minute"
    - /survey/responses: "100/hour"
    - /reports/customer/.../dimension/...: "10/hour"
    - /llm-config/{id}/test: "5/minute"

### Issue #9: No Account Lockout
- **Files**:
  - `/home/user/entrust-app/backend/app/models.py` (User model)
  - `/home/user/entrust-app/backend/app/routers/auth_router.py` (login endpoint)
- **Status**: [ ] FIXED
- **What to do**:
  - Add fields to User: failed_login_attempts, locked_until
  - Increment counter on failed login
  - Lock account after 5 failed attempts for 15 minutes
  - Reset counter on successful login
  - Create migration script

### Issue #10: Weak CORS Configuration
- **File**: `/home/user/entrust-app/backend/app/main.py`
- **Lines**: 93-104
- **Status**: [ ] FIXED
- **What to do**:
  - Explicitly list allowed origins (don't use "*")
  - Limit allowed_methods to specific methods
  - Limit allowed_headers to necessary headers only
  - Set max_age for preflight caching
  - Add documentation with secure example

---

## MEDIUM SEVERITY ISSUES (Fix within 1 month)

### Issue #11: Weak JWT Configuration
- **File**: `/home/user/entrust-app/backend/app/auth.py`
- **Lines**: 14-16
- **Status**: [ ] FIXED
- **What to do**:
  - Ensure SECRET_KEY is set in .env (not default)
  - Reduce ACCESS_TOKEN_EXPIRE_MINUTES from 1440 to 60
  - Implement refresh token mechanism
  - Add documentation on environment variables

### Issue #12: JWT in localStorage (XSS Risk)
- **File**: `/home/user/entrust-app/frontend/src/pages/Login.jsx`
- **Lines**: 23-24
- **Status**: [ ] FIXED
- **What to do**:
  - Migrate to httpOnly cookies
  - Add Secure flag for HTTPS
  - Add SameSite=Strict
  - Update API interceptor to work with cookies
  - Remove localStorage from frontend

### Issue #13: Limited Audit Logging
- **Files**: All routers, main.py
- **Status**: [ ] FIXED
- **What to do**:
  - Create AuditLog model
  - Add audit log on: login, view report, access data, config changes
  - Include: timestamp, user_id, action, resource_type, status, details, ip_address
  - Setup log retention policy
  - Create audit dashboard

---

## VERIFICATION CHECKLIST

After each fix, verify:

- [ ] **Unit tests pass** for modified code
- [ ] **Integration tests pass**
- [ ] **No secrets in logs** (grep for password, api_key, secret)
- [ ] **No secrets in responses** (test API endpoints)
- [ ] **Credentials not in URL** (check Network tab in browser)
- [ ] **Rate limiting works** (test with many requests)
- [ ] **Authorization enforced** (test cross-tenant access)
- [ ] **Input validation works** (test invalid inputs)
- [ ] **Account lockout works** (test failed attempts)
- [ ] **SSL/TLS enabled** (test with verify=True)
- [ ] **CORS properly configured** (test from different origin)
- [ ] **Audit logs recorded** (check logs for user actions)

---

## FILE LOCATIONS REFERENCE

### Backend Files:
```
/home/user/entrust-app/backend/
├── app/
│   ├── main.py                  (main.py:24-38 - creds in logs)
│   ├── auth.py                  (auth.py:14-16 - weak JWT)
│   ├── models.py                (models.py:36 - plaintext password)
│   ├── schemas.py               (schemas.py - add validation)
│   ├── llm_providers.py         (llm_providers.py:131 - verify=False)
│   └── routers/
│       ├── auth_router.py       (login endpoint)
│       ├── users.py             (users.py:32,83 - plaintext)
│       ├── customers.py         (customers.py:42 - no auth)
│       ├── survey.py            (survey.py - no validation)
│       ├── llm_config.py        (llm_config.py:80 - secrets)
│       └── reports.py           (reports.py - no auth)
└── load_secrets.py              (secrets management)
```

### Frontend Files:
```
/home/user/entrust-app/frontend/
└── src/
    ├── pages/
    │   ├── Login.jsx            (Login.jsx:16 - creds in URL)
    │   ├── LLMConfig.jsx        (hardcoded endpoints)
    │   └── UserForm.jsx
    └── api.js                   (API setup)
```

### Configuration Files:
```
/home/user/entrust-app/
├── secrets.json.example         (example only, never commit actual)
├── docker-compose.yml           (check env variables)
└── .gitignore                   (verify .env is ignored)
```

---

## TESTING COMMANDS

```bash
# Check for hardcoded secrets
grep -r "password\|secret\|api_key\|API_KEY" /home/user/entrust-app --include="*.py" --include="*.js" --include="*.jsx"

# Check for verify=False
grep -r "verify=False" /home/user/entrust-app

# Check for URL parameters in requests
grep -r "params:" /home/user/entrust-app/frontend

# Check password field usage
grep -r "password=" /home/user/entrust-app/backend --include="*.py"

# Test login with valid/invalid credentials
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"admin","password":"Welcome123!"}'

# Test if secrets are exposed
curl -X GET "http://localhost:8000/api/llm-config" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## DEPLOYMENT CHECKLIST

Before deploying to production:

- [ ] All CRITICAL issues fixed and tested
- [ ] All HIGH issues fixed and tested
- [ ] Security tests pass
- [ ] Penetration testing completed
- [ ] Secrets manager configured (not env vars)
- [ ] HTTPS/TLS enforced
- [ ] Database encryption at rest enabled
- [ ] Backups configured
- [ ] Logging and monitoring configured
- [ ] Audit logging enabled
- [ ] DLP (Data Loss Prevention) rules enabled
- [ ] WAF (Web Application Firewall) configured
- [ ] Rate limiting verified working
- [ ] CORS properly configured for production domain
- [ ] Security headers added (CSP, X-Frame-Options, etc.)

---

## ONGOING MAINTENANCE

- [ ] Weekly: Review security logs
- [ ] Monthly: Run OWASP ZAP scan
- [ ] Quarterly: Penetration testing
- [ ] Quarterly: Dependency security audit
- [ ] Annually: Full security assessment
- [ ] Continuously: Monitor for CVEs in dependencies

---

**Status**: Report generated 2025-11-13
**Severity Level**: CRITICAL - Not production-ready
**Estimated Remediation Time**: 4-6 weeks (with full team)
