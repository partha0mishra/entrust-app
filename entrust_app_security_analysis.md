# EnTrust Application - Comprehensive Security & Data Flow Analysis

## Executive Summary
The EnTrust application is a data governance survey platform with agentic LLM capabilities. This analysis identifies **5 critical security vulnerabilities**, **7 high-risk issues**, and several medium/low-risk concerns affecting authentication, authorization, and data protection.

---

# PART 1: DATA FLOW ANALYSIS

## 1. Survey Data Flow

### Flow Path: User Input → Database → LLM Analysis → Report Generation

```
┌─────────────────────┐
│  Frontend Survey    │
│   UI (React)        │
└──────────┬──────────┘
           │ POST /survey/responses
           │ {question_id, score, comment}
           ▼
┌──────────────────────┐
│  Auth Middleware     │
│  (JWT Verification)  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────┐
│ Survey Router            │
│ - save_response()        │
│ - validate user/survey   │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ Database Layer (SQLAlchemy ORM)
│ - Create/Update SurveyResponse
│ - Fields: survey_id, user_id, question_id,
│   score, comment, timestamps
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ Report Generation        │
│ (Triggered by request)   │
│ - Aggregate responses    │
│ - Calculate metrics      │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ LLM Analysis Pipeline    │
│ 1. Data chunking         │
│ 2. RAG context retrieval │
│ 3. Prompt injection      │
└──────────┬───────────────┘
           │
           ├─────────────────────────┐
           │                         │
           ▼                         ▼
┌─────────────────┐      ┌──────────────────┐
│ ChromaDB        │      │ LLM Provider     │
│ (RAG Storage)   │      │ - LOCAL/Bedrock/ │
│ Vector Search   │      │   Azure OpenAI   │
└─────────────────┘      └──────────────────┘
           │                         │
           └────────────┬────────────┘
                        ▼
        ┌──────────────────────────────┐
        │ LLM Generation:              │
        │ - Dimension summaries        │
        │ - Deep analysis              │
        │ - Comment sentiment          │
        │ - Facet analysis             │
        │ - Overall summary            │
        └──────────┬───────────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │ Report Formatting        │
        │ - Markdown generation    │
        │ - JSON structure         │
        │ - PDF export             │
        └──────────┬───────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │ Report Storage & Cache   │
        │ /app/entrust/reports/    │
        │ /app/entrust/report_json/│
        └──────────────────────────┘
```

### Data Elements in Transit:
- **User Responses**: Question scores (String: "1"-"10"), comments (String, up to 200 chars)
- **Aggregated Metrics**: Avg scores, response counts, distribution percentages
- **LLM Prompts**: Full survey data + guidance + comments injected into prompts
- **LLM Responses**: Markdown + JSON analysis
- **Reports**: PDF files with aggregated sensitive data

### Security Controls in Place:
✓ SQLAlchemy ORM (prevents SQL injection)
✓ JWT authentication on survey endpoints
✓ User isolation (responses scoped to user_id)
✓ Survey isolation (responses scoped to survey_id)

---

## 2. Authentication Flow

### Complete Auth Flow: Login → Token Generation → Protected Endpoints

```
┌─────────────────────────┐
│   1. Login Request       │
│  POST /auth/login        │
│  Query Params:           │
│  ?user_id=X&password=Y   │  ⚠️ CRITICAL: Creds in URL!
└──────────┬──────────────┘
           │
           ▼
┌──────────────────────────────┐
│   2. Authentication Handler  │
│   auth_router.py:login()     │
│   - Query user by user_id    │
│   - Verify password hash     │
│     using bcrypt (72 bytes)  │
└──────────┬───────────────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
Success      Failure
 │              │
 │          401 Unauthorized
 │          "Incorrect user ID or password"
 │
 ▼
┌─────────────────────────┐
│ 3. JWT Token Generation │
│ payload: {              │
│   "sub": user_id,       │
│   "exp": now + 1440min  │  ⚠️ LONG EXPIRY!
│ }                       │
│ signed with SECRET_KEY  │  ⚠️ WEAK DEFAULT!
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────────┐
│ 4. Token Response           │
│ {                           │
│   "access_token": "...",    │
│   "token_type": "bearer",   │
│   "user": {                 │
│     id, user_id,            │
│     username,               │
│     user_type,              │
│     password (PLAINTEXT)    │  ⚠️ CRITICAL!
│   }                         │
│ }                           │
└─────────┬───────────────────┘
          │
          ▼
┌────────────────────────────┐
│ 5. Token Storage (Client)  │
│ localStorage.setItem('token')
│ localStorage.setItem('user')
│ (No httpOnly/Secure flags)  │  ⚠️ XSS VULNERABLE!
└────────────────────────────┘
          │
          ▼
┌────────────────────────────┐
│ 6. Protected API Requests  │
│ Authorization: Bearer <token>
│ - Request interceptor      │
│   adds token from storage  │
└────────┬───────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ 7. JWT Verification         │
│ auth.get_current_user()     │
│ - Decode token              │
│ - Verify signature          │
│ - Check expiration          │
│ - Query user from DB        │
│ - Check is_deleted flag     │
└──────────┬──────────────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
 Valid       Invalid/Expired
   │             │
   │          401 Unauthorized
   │          localStorage cleared
   │          Redirect to /login
   │
   ▼
┌────────────────────┐
│ Grant Access to    │
│ Protected Resource │
└────────────────────┘
```

### Key Auth Components:

**Password Hashing:**
- Algorithm: bcrypt (with deprecated="auto")
- Truncation: 72 bytes (bcrypt limitation)
- Verification: Uses verify_password() with truncation

**JWT Configuration:**
- Algorithm: HS256 (symmetric key)
- Secret: Defaults to "your-secret-key-change-in-production"
- Expiry: 1440 minutes (24 hours) - very long
- Claims: Only "sub" (user_id) and "exp"

**Authorization Functions:**
- `get_current_user()`: Validates JWT and checks is_deleted
- `require_admin()`: Checks user_type == SYSTEM_ADMIN
- `require_customer_user()`: Checks user_type in [CXO, PARTICIPANT]
- `require_report_access()`: Checks user_type in [CXO, SALES]

---

## 3. LLM Integration Architecture

### Multi-Provider LLM System

```
┌──────────────────────────────────┐
│ LLM Configuration Layer           │
│ (Database: llm_configs table)     │
│                                  │
│ Fields:                          │
│ - purpose (unique)               │
│ - provider_type (enum)           │
│ - status ("Not Tested", etc)     │
└──────────────┬───────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
    ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐
│ LOCAL  │ │BEDROCK │ │ AZURE  │
│ LLM    │ │ AWS    │ │OpenAI  │
└────────┘ └────────┘ └────────┘
```

### LOCAL LLM Provider (LM Studio, Ollama):

```
LLMService                  LocalLLMProvider
    │                              │
    ├─ get_llm_provider(config)   │
    │        │                     │
    │        └──────────────────→  │ __init__(api_url, api_key, model_name)
    │                              │
    ├─ _call_llm(messages, tokens)│
    │        │                     │
    │        └──────────────────→  │ async call_llm(messages, max_tokens)
    │                              │
    │                              │ Prepare JSON payload:
    │                              │ {
    │                              │   "model": model_name,
    │                              │   "messages": messages,
    │                              │   "max_tokens": max_tokens
    │                              │ }
    │                              │
    │                              │ POST {api_url}
    │                              │ Headers: {
    │                              │   "Content-Type": "application/json",
    │                              │   "Authorization": "Bearer {api_key}"
    │                              │ }
    │                              │
    │                    httpx.AsyncClient
    │                              │
    │                              ▼
    │                    OpenAI-compatible API
    │                    (LM Studio, Ollama)
    │                              │
    │                              │ Response:
    │                              │ {
    │                              │   "choices": [{
    │                              │     "message": {"content": "..."}
    │                              │   }]
    │                              │ }
    │                              │
    │        ┌────────────────────┘
    │        │ Extract content
    │        ▼
    └─ Return response text
```

### AWS Bedrock Provider:

```
LLMService                  AWSBedrockProvider
    │                              │
    ├─ get_llm_provider(config)   │
    │        │                     │
    │        └──────────────────→  │ __init__(region, access_key, secret_key,
    │                              │           model_id, thinking_mode)
    │                              │
    ├─ _call_llm(messages, tokens)│
    │        │                     │
    │        └──────────────────→  │ async call_llm(messages, max_tokens)
    │                              │
    │                              │ _prepare_request_body():
    │                              │ {
    │                              │   "anthropic_version": "bedrock-2023-05-31",
    │                              │   "max_tokens": max_tokens,
    │                              │   "messages": [...],
    │                              │   "system": "...",
    │                              │   "thinking": {  ⚠️ Only if enabled
    │                              │     "type": "enabled",
    │                              │     "budget_tokens": 10000
    │                              │   },
    │                              │   "temperature": 1 (if thinking)
    │                              │ }
    │                              │
    │                              │ boto3.client('bedrock-runtime',
    │                              │   region_name, access_key, secret_key,
    │                              │   verify=False) ⚠️ CRITICAL!
    │                              │
    │                              │ invoke_model(
    │                              │   modelId, body, contentType
    │                              │ )
    │                              │
    │                              │ Response parsing:
    │                              │ content_items[0]["text"]
    │                              │
    │        ┌────────────────────┘
    │        │
    └─ Return response text
```

### Azure OpenAI Provider:

```
LLMService                  AzureOpenAIProvider
    │                              │
    ├─ get_llm_provider(config)   │
    │        │                     │
    │        └──────────────────→  │ __init__(endpoint, api_key,
    │                              │           deployment_name, api_version,
    │                              │           reasoning_effort)
    │                              │
    ├─ _call_llm(messages, tokens)│
    │        │                     │
    │        └──────────────────→  │ async call_llm(messages, max_tokens)
    │                              │
    │                              │ _get_url():
    │                              │ "{endpoint}/openai/deployments/
    │                              │  {deployment}/chat/completions
    │                              │  ?api-version={version}"
    │                              │
    │                              │ Headers:
    │                              │ {
    │                              │   "api-key": api_key ⚠️ In header
    │                              │ }
    │                              │
    │                              │ Payload varies by model type:
    │                              │ - GPT-5: max_tokens not used
    │                              │ - Others: standard max_tokens
    │                              │
    │                              │ httpx.post(url, headers, json)
    │                              │
    │        ┌────────────────────┘
    │        │
    └─ Return response text
```

### LLM Service Analysis Pipeline:

```
generate_dimension_summary()
    │
    ├─ Chunk questions by token count
    │  (MAX_CHARS_PER_CHUNK = 20,000)
    │
    ├─ For each chunk:
    │  ├─ get_rag_context(dimension) ──→ ChromaDB
    │  ├─ Build system + user prompts
    │  ├─ _call_llm() ──→ Provider
    │  └─ Parse response (markdown + JSON)
    │
    ├─ If multiple chunks:
    │  ├─ Consolidation call
    │  └─ Generate final_summary
    │
    └─ Return {
         chunk_summaries: [...],
         final_summary: "...",
         total_chunks: N
       }

generate_deep_dimension_analysis()
    │
    ├─ Format category/process/lifecycle breakdown
    ├─ Get RAG context (with survey metrics)
    ├─ Inject context into prompt
    ├─ _call_llm() ──→ Provider
    └─ Return {
         content: "...",
         rag_context: "..." (saved to DB)
       }

analyze_comments_sentiment()
    │
    ├─ Sample up to 50 comments
    ├─ Format comments text
    ├─ _call_llm() ──→ Provider
    └─ Return {
         content: "..."
       }

generate_overall_summary()
    │
    ├─ Aggregate all dimension summaries
    ├─ If large:
    │  ├─ Chunk dimensions
    │  ├─ Process each chunk
    │  └─ Consolidation call
    │
    └─ Return {
         markdown_content: "...",
         chunks_processed: N
       }
```

---

## 4. RAG Pipeline (ChromaDB + Embeddings)

### RAG Architecture:

```
Knowledge Base Files              RAG Service              ChromaDB
     │                                 │                       │
     ├─ Privacy & Compliance           │                       │
     │  └─ *.txt files                 │                       │
     │                                 │                       │
     ├─ Ethics & Bias                  │                       │
     │  └─ *.txt files                 ├─ 1. Read files        │
     │                                 │                       │
     ├─ Lineage & Traceability         ├─ 2. Chunk text       │
     │  └─ *.txt files                 │    (500 chars, 100    │
     │                                 │     overlap)          │
     ├─ Data Quality                   │                       │
     │  └─ *.txt files                 ├─ 3. Generate         │
     │                                 │    embeddings         │
     ├─ Governance & Management        │    (all-MiniLM-      │
     │  └─ *.txt files                 │     L6-v2)            │
     │                                 │                       │
     ├─ Security & Access              │ 4. Create chunk IDs  │
     │  └─ *.txt files                 │    (MD5 hash)        │
     │                                 │                       │
     ├─ Metadata & Documentation       │ 5. Store in DB       │
     │  └─ *.txt files                 │    (PersistentClient)│
     │                                 │                       │
     └─ Organizational Maturity        │                       │
        └─ *.txt files                 │                       │
                                       │
                                       └──────────────────────→ Collection:
                                                               "data_governance"
                                                                    │
                                                                    ├─ ids
                                                                    ├─ documents
                                                                    ├─ embeddings
                                                                    └─ metadatas
                                                                       ├─ dimension
                                                                       ├─ dimension_key
                                                                       ├─ source_file
                                                                       ├─ chunk_index
                                                                       └─ total_chunks
```

### RAG Retrieval Flow (During LLM Analysis):

```
get_dimension_context(dimension)
    │
    ├─ Query: "Best practices for {dimension}"
    │
    ├─ Encode query:
    │  SentenceTransformer.encode([query])
    │
    ├─ collection.query(
    │    query_embeddings=[...],
    │    n_results=5,
    │    where={"dimension": dimension}
    │  )
    │
    ├─ Also retrieve Organizational Maturity
    │  (n_results=2, include_maturity=True)
    │
    └─ Format context:
       "### RAG-ENHANCED CONTEXT: Industry Standards
        
        1. [source_file]
        {chunk_text}
        
        2. [source_file]
        {chunk_text}
        
        ...
        
        **Maturity Model Context:**
        {maturity_chunk}"

Injected into LLM Prompt:
    │
    └─ System prompt + RAG context + User prompt
       └─ Sent to LLM with instruction to use context
```

### Security Considerations for RAG:
- **Vector Storage**: ChromaDB persists to disk (/app/chroma_db)
- **Embeddings**: Using sentence-transformers (CPU-based)
- **No Access Control**: RAG context is shared across all customers
- **Sensitive Data Risk**: If knowledge base contains sensitive info, it's indexed

---

## 5. Report Generation Pipeline

### Complete Report Generation Flow:

```
POST /reports/customer/{customer_id}/dimension/{dimension}
    │
    ├─ 1. Authenticate & Authorize
    │  ├─ Verify JWT
    │  └─ Check require_report_access() [CXO, SALES]
    │
    ├─ 2. Fetch Survey Data
    │  ├─ Get survey by customer_id
    │  ├─ Fetch all responses
    │  └─ Get all questions
    │
    ├─ 3. Aggregate Metrics
    │  ├─ Calculate dimension avg scores
    │  ├─ Aggregate by category
    │  ├─ Aggregate by process
    │  ├─ Aggregate by lifecycle stage
    │  └─ Collect all comments
    │
    ├─ 4. Check Cache
    │  └─ get_cached_report(customer_code, dimension)
    │     If fresh: return cached JSON
    │
    ├─ 5. Generate LLM Analyses (if not cached)
    │  │
    │  ├─ a) Deep Dimension Analysis
    │  │   └─ LLMService.generate_deep_dimension_analysis()
    │  │
    │  ├─ b) Analyze by Category
    │  │   └─ For each category:
    │  │      LLMService.analyze_facet('category', name, data)
    │  │
    │  ├─ c) Analyze by Process
    │  │   └─ For each process:
    │  │      LLMService.analyze_facet('process', name, data)
    │  │
    │  ├─ d) Analyze by Lifecycle
    │  │   └─ For each stage:
    │  │      LLMService.analyze_facet('lifecycle_stage', name, data)
    │  │
    │  ├─ e) Sentiment Analysis
    │  │   └─ LLMService.analyze_comments_sentiment(comments)
    │  │
    │  ├─ f) Use Agentic Service (if enabled)
    │  │   └─ AgenticReportService.generate_comprehensive_report()
    │  │      ├─ SurveyParser agent
    │  │      ├─ MaturityAssessor agent
    │  │      ├─ ReportGenerator agent
    │  │      ├─ SelfCritic agent
    │  │      └─ PDFFormatter agent
    │  │
    │  └─ g) Fall back to non-agentic if disabled
    │
    ├─ 6. Format Report
    │  ├─ create_markdown_report()
    │  │  ├─ Title + metadata
    │  │  ├─ Executive summary
    │  │  ├─ Dimension analysis
    │  │  ├─ Category/Process/Lifecycle breakdowns
    │  │  ├─ Comment analysis
    │  │  └─ Recommendations
    │  │
    │  └─ Build JSON report structure
    │
    ├─ 7. Save Reports
    │  ├─ save_reports()
    │  ├─ Markdown: /app/entrust/reports/{customer_code}/{dimension}_report_{date}.md
    │  ├─ JSON: /app/entrust/report_json/{customer_code}/{dimension}_report_{date}.json
    │  └─ Log success/error
    │
    └─ 8. Return Response
       ├─ API returns JSON report
       └─ Frontend can render or export to PDF

GET /reports/customer/{customer_id}/dimension/{dimension}/download
    │
    ├─ Fetch report from file system
    ├─ Generate PDF from markdown (using agentic PDF formatter)
    └─ Return blob for browser download
```

### Report Structure:

```json
{
  "dimension": "Data Privacy & Compliance",
  "customer_code": "ACME",
  "customer_name": "ACME Corp",
  "report_date": "2024-11-13",
  "overall_metrics": {
    "avg_score": 7.2,
    "response_rate": 85.5,
    "respondent_count": 17,
    "score_distribution": {}
  },
  "dimension_analysis": {
    "content": "Markdown analysis...",
    "rag_context": "Injected RAG context..."
  },
  "category_analysis": {
    "category_name": {
      "avg_score": 7.5,
      "count": 10,
      "respondents": 5,
      "comments": [...],
      "score_distribution": {},
      "questions": [...]
    }
  },
  "process_analysis": {...},
  "lifecycle_analysis": {...},
  "comment_insights": {
    "sentiment": "Positive/Mixed/Negative",
    "themes": [...],
    "detailed_analysis": "..."
  },
  "agentic_analysis": {
    "agents_executed": ["Parser", "Assessor", "Generator"],
    "sections": [...]
  }
}
```

---

# PART 2: SECURITY ANALYSIS

## CRITICAL VULNERABILITIES (Must Fix Immediately)

### 1. CRITICAL: Credentials Transmitted as URL Parameters

**Location**: `frontend/src/pages/Login.jsx` line 16

**Vulnerability**:
```javascript
const response = await fetch(`${API_URL}/api/auth/login?user_id=${userId}&password=${password}`, {
  method: 'POST',
});
```

**Risk**:
- Passwords exposed in browser history
- Logged in web server access logs
- Visible to HTTP proxies/CDNs
- Cached in browser
- May appear in referrer headers
- Screenshots/screen sharing exposes credentials

**Impact**: CRITICAL - Complete authentication bypass possible

**Remediation**:
```javascript
const response = await fetch(`${API_URL}/api/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ user_id: userId, password: password })
});
```

Also update backend `auth_router.py`:
```python
@router.post("/login")
async def login(credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    # Accept JSON body instead of query params
    user = db.query(models.User).filter(
        models.User.user_id == credentials.user_id,
        models.User.is_deleted == False
    ).first()
    ...
```

---

### 2. CRITICAL: Plain Text Passwords Stored in Database

**Locations**: 
- `backend/app/models.py` lines 36: `password = Column(Text, nullable=True)`
- `backend/app/routers/users.py` lines 32: `password=plain_password`
- `backend/app/routers/users.py` lines 83: `db_user.password = update_data['password']`

**Vulnerability**:
```python
# models.py
class User(Base):
    password_hash = Column(String(255), nullable=False)  # Good
    password = Column(Text, nullable=True)  # BAD - Plain text!

# users.py - storing plain password
db_user = models.User(
    password_hash=hashed_password,
    password=plain_password  # Stores plain text for admin viewing
)
```

**Risk**:
- Database breach exposes all passwords in plain text
- Violates GDPR, PCI-DSS, HIPAA
- Admin panels can display passwords
- Password reset mechanism could leak credentials

**Impact**: CRITICAL - All user accounts compromised if DB is breached

**Remediation**:
```python
# Remove password field entirely
# password = Column(Text, nullable=True)  # DELETE THIS

# For password viewing/reset:
# 1. Use password reset tokens instead
# 2. Never store plain passwords
# 3. For admin viewing, show "Password reset link" instead

class User(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), unique=True)
    password_hash = Column(String(255), nullable=False)
    # NO password field - REMOVE IT
```

---

### 3. CRITICAL: Default Admin Credentials Printed to Logs

**Location**: `backend/app/main.py` lines 24-38

**Vulnerability**:
```python
print("[INIT]    User ID: admin")
print("[INIT]    Password: Welcome123!")
```

**Risk**:
- Credentials visible in application startup logs
- Logs stored in container logs, syslog
- Exposed in Docker logs, Kubernetes logs
- Visible to anyone with log access
- Default credentials never changed in production

**Impact**: CRITICAL - Trivial unauthorized access to admin account

**Remediation**:
```python
# Remove printed credentials entirely
print("[INIT] [OK] Default admin user created!")
print("[INIT]    User ID: admin")
# DO NOT print password!
# Instead, suggest password reset on first login
# or send to secure location
```

Implement:
- Force password reset on first login for default admin
- Or generate random password and send via secure channel
- Never print credentials to logs

---

### 4. CRITICAL: SSL/TLS Verification Disabled for AWS Bedrock

**Location**: `backend/app/llm_providers.py` line 131

**Vulnerability**:
```python
self._client = boto3.client(
    'bedrock-runtime',
    region_name=self.region,
    aws_access_key_id=self.access_key_id,
    aws_secret_access_key=self.secret_access_key,
    config=config,
    verify=False  # DANGEROUS - Disables SSL/TLS verification!
)
```

**Risk**:
- Vulnerable to Man-in-the-Middle (MITM) attacks
- Attacker can intercept and modify API requests
- AWS credentials transmitted without verification
- LLM prompts containing sensitive data exposed

**Impact**: CRITICAL - MITM can steal credentials and data, modify responses

**Remediation**:
```python
# Remove verify=False (defaults to True)
self._client = boto3.client(
    'bedrock-runtime',
    region_name=self.region,
    aws_access_key_id=self.access_key_id,
    aws_secret_access_key=self.secret_access_key,
    config=config
    # verify=True is default and correct
)
```

If there's a specific reason for disabling (like custom CA), use:
```python
verify='/path/to/ca-bundle.crt'  # Path to certificate bundle
```

---

### 5. CRITICAL: AWS and Azure Credentials Returned in API Response

**Location**: `backend/app/routers/llm_config.py` lines 75-81

**Vulnerability**:
```python
@router.get("/", response_model=List[schemas.LLMConfig])
def list_llm_configs(...):
    configs = db.query(models.LLMConfig).all()
    return configs  # Returns ALL fields including secrets!
```

**Data Exposed**:
```python
{
  "aws_access_key_id": "AKIA...",
  "aws_secret_access_key": "wJalr...",
  "azure_api_key": "key-...",
  "api_key": "...",
  ...
}
```

**Risk**:
- AWS and Azure credentials returned to frontend
- Credentials stored in browser localStorage
- Credentials sent in API responses (logs, caches, proxies)
- Frontend can access credentials via JavaScript

**Impact**: CRITICAL - Cloud credentials compromised

**Remediation**:

Option 1: Never expose secrets to frontend
```python
@router.get("/", response_model=List[schemas.LLMConfigSafe])
def list_llm_configs(...):
    # Return only config metadata, NOT secrets
    configs = db.query(models.LLMConfig).all()
    return [{
        "id": c.id,
        "purpose": c.purpose,
        "provider_type": c.provider_type,
        "model_name": c.model_name,
        "status": c.status,
        # Omit: aws_access_key_id, aws_secret_access_key, azure_api_key, api_key
    } for c in configs]
```

Option 2: Encrypt credentials server-side
```python
class LLMConfig(Base):
    # Encrypt sensitive fields
    aws_access_key_id = Column(String(500))  # Encrypted
    aws_secret_access_key = Column(String(500))  # Encrypted
    
# Use encryption at rest (e.g., Field-level encryption)
# Never decrypt and return to client
```

---

## HIGH SEVERITY VULNERABILITIES

### 6. HIGH: Insufficient Input Validation

**Locations**: Multiple endpoints

**Issues**:

a) Survey Score Field (String instead of Integer):
```python
# models.py
class SurveyResponse(Base):
    score = Column(String(10))  # Should be Integer with range 1-10
    comment = Column(String(200))  # No length validation at DB level
```

**Attack**:
```
POST /survey/responses
{
  "question_id": 1,
  "score": "INVALID_VALUE",
  "comment": "A" * 50000  # Excessive size
}
```

b) No input validation on customer codes:
```python
@router.post("/")
def create_customer(customer: schemas.CustomerCreate, ...):
    # No validation on customer.customer_code format
    # No check for injection attacks
```

c) No pagination limits on list endpoints:
```python
@router.get("/")
def list_customers(skip: int = 0, limit: int = 100, ...):
    # limit=100 could allow large data exposure
    # No maximum limit enforced
```

**Remediation**:
```python
# Fix score field
class SurveyResponse(Base):
    score = Column(Integer)  # Integer 1-10

# Add Pydantic validation
class SurveyResponseCreate(BaseModel):
    question_id: int
    score: int = Field(ge=1, le=10)  # Range validation
    comment: str = Field(max_length=200)  # Length validation

# Enforce pagination limits
@router.get("/")
def list_customers(skip: int = Query(0, ge=0),
                  limit: int = Query(100, ge=1, le=100), ...):
    # limit capped at 100
```

---

### 7. HIGH: Missing Authorization Checks

**Location**: `backend/app/routers/customers.py` lines 37-52, 54-72

**Vulnerability**:
```python
@router.get("/", response_model=List[schemas.Customer])
def list_customers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)  # Any authenticated user!
):
    """Available to all authenticated users."""
    customers = db.query(models.Customer).filter(
        models.Customer.is_deleted == False
    ).offset(skip).limit(limit).all()
    return customers
```

**Issue**: Any authenticated user (even CXO from a different company) can see ALL customers

**Risk**:
- Data leakage across customers
- CXO sees competitors' data
- Participant can enumerate all organizations

**Current Authorization Model**:
- `require_admin`: Only SYSTEM_ADMIN
- `require_customer_user`: CXO or PARTICIPANT (any customer!)
- `require_report_access`: CXO or SALES (any customer!)

**Missing Checks**:
- CXO should only see own customer's data
- PARTICIPANT should only see own customer's surveys
- SALES should only see authorized customer reports
- No tenant isolation in most endpoints

**Remediation**:
```python
@router.get("/", response_model=List[schemas.Customer])
def list_customers(..., current_user: models.User = Depends(auth.get_current_user)):
    """Only return current user's customer"""
    if current_user.user_type == models.UserType.SYSTEM_ADMIN:
        # Admin can see all
        return db.query(models.Customer).filter(...).all()
    elif current_user.user_type == models.UserType.CXO:
        # CXO only sees own customer
        if not current_user.customer_id:
            raise HTTPException(status_code=400, detail="...")
        customer = db.query(models.Customer).filter(
            models.Customer.id == current_user.customer_id
        ).first()
        return [customer] if customer else []
    else:
        raise HTTPException(status_code=403, detail="Not authorized")
```

---

### 8. HIGH: No Rate Limiting

**Vulnerable Endpoints**:
- `/auth/login` - Brute force vulnerability
- `/survey/responses` - Can spam unlimited responses
- `/reports/customer/{id}/dimension/{dim}` - Can trigger unlimited LLM calls
- `/llm-config/{id}/test` - Can spam LLM providers

**Risk**:
- Brute force login attacks
- Denial of Service (LLM API abuse)
- Cost explosion from unlimited LLM calls
- Database flooding with spam responses

**Remediation**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# In auth router
@router.post("/login")
@limiter.limit("5/minute")  # 5 attempts per minute
def login(...):
    ...

# In survey router
@router.post("/responses")
@limiter.limit("100/hour")  # 100 responses per hour
def save_response(...):
    ...

# In reports router
@router.get("/customer/{id}/dimension/{dim}")
@limiter.limit("10/hour")  # 10 generations per hour
def get_dimension_report(...):
    ...
```

---

### 9. HIGH: No Account Lockout Mechanism

**Vulnerability**: 
- No failed login attempt tracking
- No account lockout after N attempts
- No CAPTCHA or additional verification

**Risk**:
- Brute force attacks can continue indefinitely
- Weak passwords can be guessed

**Remediation**:
```python
class User(Base):
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)

def login(user_id, password, db):
    user = db.query(models.User).filter(...).first()
    
    # Check if locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(403, "Account locked. Try again later.")
    
    # Verify password
    if not auth.verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        
        # Lock after 5 failed attempts
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=15)
        
        db.commit()
        raise HTTPException(401, "Invalid credentials")
    
    # Success - reset counter
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()
    ...
```

---

## MEDIUM SEVERITY VULNERABILITIES

### 10. MEDIUM: Weak CORS Configuration

**Location**: `backend/app/main.py` lines 93-104

**Configuration**:
```python
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,  # Allows cross-origin credentialed requests
    allow_methods=["*"],  # All HTTP methods
    allow_headers=["*"],  # All headers
)
```

**Risks**:
- If `ALLOWED_ORIGINS="*"`: Any website can access API with credentials
- `allow_methods=["*"]` allows DELETE, PATCH on any endpoint
- Vulnerable to CSRF if not configured correctly
- Wide allow_headers can bypass security headers

**Remediation**:
```python
ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
    # Never use "*" with allow_credentials=True
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=600,  # Cache preflight for 10 minutes
)
```

---

### 11. MEDIUM: Weak Default JWT Configuration

**Location**: `backend/app/auth.py` lines 14-16

**Issues**:
```python
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
# ^ Default secret is weak!

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
# ^ 1440 minutes = 24 hours = VERY LONG!
```

**Risks**:
- Default secret easily guessable
- 24-hour token expiry means:
  - Token theft = 24 hours of access
  - Long time to detect compromised tokens
  - No way to revoke tokens early

**Remediation**:
```python
# In .env or deployment config
SECRET_KEY=<generate-strong-random-key>  # At least 256 bits
ACCESS_TOKEN_EXPIRE_MINUTES=60  # 1 hour is more reasonable

# For better security, implement refresh tokens
# Issue short-lived access tokens + long-lived refresh tokens
```

---

### 12. MEDIUM: XSS Vulnerability - JWT in localStorage

**Location**: `frontend/src/pages/Login.jsx` lines 23-24

**Code**:
```javascript
localStorage.setItem('token', data.access_token);
localStorage.setItem('user', JSON.stringify(data.user));
```

**Vulnerability**:
```javascript
// Any JavaScript can access localStorage
const token = localStorage.getItem('token');  // Vulnerable to XSS

// If page is XSS-vulnerable, attacker can:
// 1. Steal JWT token
// 2. Steal user object (including plain password)
// 3. Make authenticated API calls
```

**Risk**:
- Plain text password stored in localStorage accessible to XSS
- JWT theft = full account access

**Remediation**:

Option 1: Use httpOnly Cookies (Best):
```javascript
// Backend sets cookie
response.headers['Set-Cookie'] = 'token=...;HttpOnly;Secure;SameSite=Strict'

// Frontend doesn't need to store anything
// Cookies automatically sent with requests
```

Option 2: If using localStorage:
```python
# Never return plain password in login response
class User(BaseModel):
    id: int
    user_id: str
    username: str
    user_type: UserType
    customer_id: Optional[int]
    # Remove: password field

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User  # Without password
```

---

### 13. MEDIUM: Limited Audit Logging

**Observations**:
- LLM API calls are logged with info level
- Configuration changes are logged
- But NO audit trail for:
  - Who accessed which reports
  - Who viewed customer data
  - Data access patterns
  - Configuration changes over time
  - Password resets/changes

**Recommendation**:
```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(50))  # "LOGIN", "VIEW_REPORT", "UPDATE_CONFIG"
    resource_type = Column(String(50))  # "report", "customer", "config"
    resource_id = Column(Integer)
    status = Column(String(20))  # "SUCCESS", "FAILED"
    details = Column(Text)  # JSON with additional context
    ip_address = Column(String(50))
    user_agent = Column(String(500))
```

---

## LOW SEVERITY VULNERABILITIES

### 14. LOW: Verbose Error Messages in Logs

**Location**: Various error handlers

**Issue**:
```python
logger.error(f"AWS Bedrock API Error: {str(e)}", exc_info=True)
# exc_info=True includes full stack trace, may contain sensitive data
```

**Recommendation**:
```python
# Generic message to user
raise HTTPException(status_code=500, detail="Internal server error")

# Detailed logging only for admins
logger.error(f"Service error occurred", exc_info=True)  # Log trace
# Don't expose full error details to client
```

---

# SUMMARY TABLE

| ID | Severity | Issue | File | Line |
|----|----------|-------|------|------|
| 1 | CRITICAL | Credentials in URL params | Login.jsx | 16 |
| 2 | CRITICAL | Plain text passwords in DB | models.py, users.py | 36, 32 |
| 3 | CRITICAL | Default creds in logs | main.py | 38 |
| 4 | CRITICAL | SSL/TLS verify=False | llm_providers.py | 131 |
| 5 | CRITICAL | Secrets in API response | llm_config.py | 80 |
| 6 | HIGH | Missing input validation | models.py, survey.py | - |
| 7 | HIGH | Missing auth checks | customers.py, reports.py | 42-52 |
| 8 | HIGH | No rate limiting | all routers | - |
| 9 | HIGH | No account lockout | auth.py | - |
| 10 | MEDIUM | Weak CORS config | main.py | 93-104 |
| 11 | MEDIUM | Weak JWT defaults | auth.py | 14-16 |
| 12 | MEDIUM | XSS: JWT in localStorage | Login.jsx | 23-24 |
| 13 | MEDIUM | Limited audit logging | - | - |
| 14 | LOW | Verbose error messages | Various | - |

---

# RECOMMENDATIONS

## Immediate Actions (CRITICAL)
1. Move login credentials to request body
2. Remove plain text password storage
3. Don't print credentials to logs
4. Enable SSL/TLS verification
5. Don't expose secrets in API responses

## Short Term (HIGH)
1. Add input validation
2. Implement tenant isolation
3. Add rate limiting
4. Implement account lockout
5. Use httpOnly cookies for JWT

## Medium Term (MEDIUM)
1. Review and tighten CORS
2. Implement audit logging
3. Add password reset mechanism
4. Implement CSRF protection
5. Add monitoring/alerting

## Long Term
1. Implement OAuth2/OpenID Connect
2. Add multi-factor authentication
3. Regular security audits
4. Penetration testing
5. Secrets management (HashiCorp Vault, etc.)

