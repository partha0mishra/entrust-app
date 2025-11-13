# Audit Findings - Organized by File

## Critical Files with Multiple Issues

### auth.py (6 critical issues)

| Issue | Line | Type | CVSS | Description |
|-------|------|------|------|-------------|
| #35 | 14-16 | Security | 8.6 | Default JWT secret "your-secret-key-change-in-production" |
| #36 | 22-24 | Security | 8.2 | Weak encryption key derivation with padding not KDF |
| #37 | 15 | Security | High | HS256 symmetric algorithm instead of RS256 |
| #38 | N/A | Security | High | No token revocation mechanism |
| #39 | 29-31 | Usability | Low | Silent password truncation at 72 bytes |
| #9 | 29-34 | Security | Good | Correct: Single error message prevents user enumeration ✓ |

**Recommendation:** Complete rewrite of token handling and encryption

---

### models.py (7 issues)

| Issue | Line | Type | CVSS | Description |
|-------|------|------|------|-------------|
| #1 | 36 | Security | 9.8 | Plaintext password field `User.password` |
| #2 | 25 (main.py) | Security | 9.1 | Hardcoded default password "Welcome123!" |
| #3 | 29-44 | Design | Medium | No email field; relies on user_id |
| #4 | 7-11 | Design | Medium | String-based UserType enum |
| #5 | All | Performance | High | Missing indexes on foreign keys |
| #6 | 126-140 | Integrity | High | No UNIQUE constraint on SurveyResponse |
| #7 | N/A | Retention | Medium | Missing soft delete on Question/Survey/Response |

**Recommendation:** Complete redesign of User model and add proper indexing

---

### database.py (3 critical issues)

| Issue | Line | Type | CVSS | Description |
|-------|------|------|------|-------------|
| #40 | 8-10 | Security | 8.6 | Default connection string with credentials |
| #41 | 13 | Performance | High | No connection pool configuration |
| #42 | N/A | Reliability | Medium | No database initialization verification |

**Recommendation:** Use environment variables, add pool tuning, add startup checks

---

### users.py (2 critical issues)

| Issue | Line | Type | CVSS | Description |
|-------|------|------|------|-------------|
| #19 | 24-33 | Security | 9.8 | Storing plaintext passwords |
| #20 | 79 | Integrity | Medium | Missing validation on user updates |

**Recommendation:** Remove plaintext password storage, validate critical fields

---

### llm_config.py (2 critical issues)

| Issue | Line | Type | CVSS | Description |
|-------|------|------|------|-------------|
| #22 | N/A | Security | 9.8 | Secrets stored in database (API keys, AWS credentials) |
| #23 | 20-73 | Usability | Medium | No validation of required config fields |

**Recommendation:** Move to AWS Secrets Manager or Azure Key Vault

---

## High Priority Files

### reports.py (4 issues)

| Issue | Line | Type | Severity | Description |
|-------|------|------|----------|-------------|
| #14 | 97-110 | Code Quality | Low | 13 function parameters |
| #15 | 441-475 | Reliability | High | No retry logic on LLM failures |
| #16 | 343-349 | Performance | High | `.all()` loads entire dataset to memory |
| #17 | 447-450 | Maintainability | Medium | Timeout values scattered as magic numbers |
| #18 | 277-283 | Security | High | No customer access validation for CXO |

**Impact:** Memory issues at scale, potential data exposure

---

### survey.py (3 issues)

| Issue | Line | Type | Severity | Description |
|-------|------|------|----------|-------------|
| #11 | 64-103 | Performance | High | N+1 queries in progress tracking |
| #12 | 227, 233 | Quality | Medium | Silent comment truncation |
| #13 | 320-333 | Concurrency | High | Race condition on submission status |

**Impact:** Slow survey pages, data inconsistency in concurrent scenarios

---

### llm_service.py (4 issues)

| Issue | Line | Type | Severity | Description |
|-------|------|------|----------|-------------|
| #24 | 35-38 | Design | Medium | Hardcoded "4 chars per token" estimation |
| #25 | 164 | Security | Medium | Unsafe regex for JSON parsing |
| #26 | All | Observability | Medium | Missing logging on LLM calls |
| #27 | 39 | Maintainability | Low | Magic number timeout (180 seconds) |

**Impact:** Fragile chunking, debugging difficulties, no cost tracking

---

### rag.py (4 issues)

| Issue | Line | Type | Severity | Description |
|-------|------|------|----------|-------------|
| #28 | 451-456 | Concurrency | High | Missing thread lock on singleton |
| #29 | 209-212 | Reliability | Medium | Silent failures on missing knowledge base |
| #30 | 40 | Flexibility | Medium | Hardcoded embedding model |
| #31 | 258-259 | Performance | Medium | No embedding cache |

**Impact:** Potential race conditions, inflexible configuration

---

## Medium Priority Files

### report_utils.py (3 issues)

| Issue | Line | Type | Severity | Description |
|-------|------|------|----------|-------------|
| #32 | 24-25 | Flexibility | Medium | Hardcoded report path "/app/entrust" |
| #33 | 389-430 | Storage | Medium | No cleanup of cached reports |
| #34 | 29-51 | Maintainability | Low | Inconsistent dimension mapping |

---

### auth_router.py (1 issue)

| Issue | Line | Type | Severity | Description |
|-------|------|------|----------|-------------|
| #8 | 9-50 | Security | High | Missing rate limiting on login |

**Risk:** Brute force attacks possible

---

### customers.py (1 issue)

| Issue | Line | Type | Severity | Description |
|-------|------|------|----------|-------------|
| #21 | All | Compliance | Medium | Missing audit logging |

**Impact:** No audit trail for compliance

---

### requirements.txt (4 issues)

| Issue | Item | Type | Severity | Description |
|-------|------|------|----------|-------------|
| #43 | Line 15 | Maintenance | Low | Unused openai dependency |
| #44 | All | Security | Medium | Fixed version pins prevent auto-patching |
| #45 | N/A | Compliance | Medium | No security scanning integration |
| #46 | N/A | Deployment | High | Heavy ML dependencies (torch, transformers) |

**Impact:** Large Docker images, CVE exposure

---

## Summary Statistics

### Issues by File

```
auth.py                    6 issues
models.py                  7 issues
database.py                3 issues
users.py                   2 issues
llm_config.py              2 issues
reports.py                 5 issues
survey.py                  3 issues
llm_service.py             4 issues
rag.py                      4 issues
report_utils.py            3 issues
auth_router.py             1 issue
customers.py               1 issue
requirements.txt           4 issues
=====================================
TOTAL                     45 issues
```

### Issues by Severity

- **CRITICAL (CVSS 8.6+):** 6 issues
- **HIGH (CVSS 7.0-8.5):** 12 issues
- **MEDIUM (CVSS 4.0-6.9):** 20 issues
- **LOW (CVSS 1.0-3.9):** 7 issues

### Issues by Category

- **Security:** 16 issues
- **Performance:** 8 issues
- **Data Integrity:** 7 issues
- **Concurrency:** 2 issues
- **Code Quality:** 4 issues
- **Maintainability:** 5 issues
- **Compliance:** 2 issues
- **Configuration:** 1 issue

---

## Quick Fix Checklist

### Can Be Fixed in < 1 Hour
- [ ] Remove hardcoded default password
- [ ] Make SECRET_KEY required environment variable
- [ ] Add connection pool configuration
- [ ] Add database initialization verification
- [ ] Make report path configurable
- [ ] Remove unused openai dependency
- [ ] Add rate limiting to login endpoint

### Can Be Fixed in 1-4 Hours
- [ ] Fix weak encryption key derivation
- [ ] Add database indexes
- [ ] Fix N+1 queries
- [ ] Add thread-safety to RAG singleton
- [ ] Add dimension access validation
- [ ] Fix regex JSON parsing
- [ ] Make embedding model configurable

### Requires 4+ Hours
- [ ] Remove plaintext password storage (full redesign)
- [ ] Move secrets to vault
- [ ] Implement token refresh/revocation
- [ ] Fix race conditions
- [ ] Add comprehensive logging
- [ ] Optimize report generation
- [ ] Add retry logic to LLM calls

---

## Notes for Development Teams

1. **Start with security issues** - Address the 6 CRITICAL issues first
2. **Then tackle performance** - Database indexes will have biggest impact
3. **Concurrent development possible** - Can work on different files in parallel
4. **Testing critical** - Add unit tests as you fix issues to prevent regression
5. **Document changes** - Update DEPLOYMENT.md with security requirements

