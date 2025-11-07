# RAG Integration for Data Governance Survey Analysis

This document describes the RAG (Retrieval-Augmented Generation) integration for enhancing survey analysis with industry standards and best practices.

## Overview

The RAG integration enriches LLM-generated reports by injecting relevant knowledge from curated documents covering:

- **Data Privacy & Compliance**: GDPR, CCPA, ISO 27701
- **Data Ethics & Bias**: AI ethics guidelines, bias mitigation frameworks
- **Data Lineage & Traceability**: DAMA-DMBOK lineage standards
- **Data Value & Lifecycle Management**: Data lifecycle frameworks
- **Data Governance & Management**: DAMA-DMBOK governance framework
- **Data Security & Access**: NIST, ISO 27001 security standards
- **Metadata & Documentation**: Metadata standards, data catalogs
- **Data Quality**: ISO 8000, TDQM frameworks
- **Organizational Maturity**: DAMA-DMBOK, Gartner EIM, CMMI/DMM maturity models

## Architecture

### Components

1. **Knowledge Base** (`Knowledge/` directory)
   - Organized by dimension
   - Contains curated text documents
   - Populated via `setup_knowledge.py`

2. **Vector Store** (ChromaDB)
   - Persistent storage in `chroma_db/`
   - Embeddings using `sentence-transformers/all-MiniLM-L6-v2`
   - Supports metadata filtering by dimension

3. **RAG Service** (`app/rag.py`)
   - Document chunking (500 chars, 100 char overlap)
   - Vector embedding and storage
   - Context retrieval with semantic search

4. **LLM Integration** (`app/llm_service.py`)
   - Automatic RAG context injection into prompts
   - Context-aware retrieval based on survey metrics

## Setup Instructions

### Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install:
- `chromadb==0.4.22`: Vector database
- `sentence-transformers==2.3.1`: Embedding model
- `torch`: PyTorch for sentence-transformers

### Step 2: Download and Prepare Knowledge Base

```bash
python setup_knowledge.py
```

This script:
- Creates `Knowledge/` directory structure
- Downloads curated documents from public sources
- Uses fallback content if downloads fail
- Organizes files by dimension

**Expected Output**:
```
Knowledge/
├── privacy_compliance/
│   ├── gdpr_overview.txt
│   └── ccpa_overview.txt
├── ethics_bias/
│   └── ai_ethics_bias.txt
├── maturity/
│   ├── dama_dmbok_maturity.txt
│   ├── gartner_eim_maturity.txt
│   └── ibm_maturity.txt
└── ... (other dimensions)
```

### Step 3: Ingest Knowledge Base into Vector Store

```bash
python -m app.rag
```

Or use the `--force` flag to re-ingest:

```bash
python -m app.rag --force
```

This will:
- Load all documents from `Knowledge/`
- Chunk documents (500 chars per chunk)
- Generate embeddings using sentence-transformers
- Store in ChromaDB (`chroma_db/` directory)

**Expected Output**:
```
[INFO] Initializing ChromaDB...
[INFO] Processing dimension: Data Privacy & Compliance
[INFO]   Created 15 chunks from gdpr_overview.txt
[INFO]   ✓ Ingested 15 chunks
[INFO] Ingestion Complete!
[INFO] Files processed: 25
[INFO] Total chunks created: 450
```

### Step 4: Verify Setup

Run the test suite:

```bash
python test_rag.py
```

This validates:
- RAG initialization
- Statistics retrieval
- Context retrieval for various dimensions
- Edge case handling

**Expected Output**:
```
TEST SUMMARY
================================================================================
  ✓ PASS: RAG Initialization
  ✓ PASS: RAG Statistics
  ✓ PASS: Basic Retrieval
  ✓ PASS: Dimension Context
  ✓ PASS: Empty Query Edge Case
  ✓ PASS: Invalid Dimension Edge Case
  ✓ PASS: Maturity Context

  Total: 7/7 tests passed
```

## Usage

### Automatic Integration

RAG is automatically integrated into the LLM service. When generating reports:

1. **Survey data** is analyzed as usual
2. **RAG context** is retrieved based on:
   - Dimension name
   - Survey metrics (avg score, response rate)
3. **Context is injected** into LLM prompts
4. **LLM generates** enhanced analysis grounded in standards

### Manual Usage

#### Retrieve Context for a Dimension

```python
from app.rag import get_dimension_context

context = get_dimension_context(
    dimension="Data Privacy & Compliance",
    survey_summary="Average score: 6.5/10, Low scores in encryption"
)
print(context)
```

#### Basic Context Retrieval

```python
from app.rag import retrieve_context

context = retrieve_context(
    query="What are GDPR requirements for data privacy?",
    dimension="Data Privacy & Compliance",
    top_k=3
)
print(context)
```

#### Get RAG Statistics

```python
from app.rag import get_rag_stats

stats = get_rag_stats()
print(f"Total documents: {stats['total_documents']}")
print(f"By dimension: {stats['by_dimension']}")
```

## Enhanced Report Features

### New Maturity Assessment Section

All dimension reports now include:

1. **Maturity Level Analysis**
   - Maps survey scores to maturity frameworks:
     - DAMA-DMBOK (1-5 levels)
     - Gartner EIM (5 stages)
     - CMMI/DMM (5 levels)
   - Provides overall maturity score

2. **Gap Analysis**
   - Identifies gaps between current and target maturity
   - Prioritizes critical gaps
   - Links to survey evidence

3. **Maturity Progression Roadmap**
   - Short-term (0-6 months): Quick wins
   - Medium-term (6-12 months): Capability building
   - Long-term (12-24 months): Excellence initiatives
   - Framework-aligned recommendations

4. **Success Indicators**
   - Measurable KPIs for tracking progress
   - Target values at 6, 12, and 24 months

### Overall Report Enhancements

The overall report includes:

1. **Enterprise Maturity Profile**
   - Synthesizes maturity across all dimensions
   - Identifies cross-dimension patterns
   - Calculates enterprise maturity score

2. **Unified Maturity Strategy**
   - Phased approach (3 phases)
   - Cross-functional initiatives
   - Change management considerations

## Configuration

### Embedding Model

To change the embedding model, modify `app/rag.py`:

```python
# Default: all-MiniLM-L6-v2 (fast, good quality)
service = RAGService(embedding_model="all-MiniLM-L6-v2")

# Alternative: Use a larger model for better quality
service = RAGService(embedding_model="all-mpnet-base-v2")
```

### Chunk Size and Overlap

Modify chunking parameters in `app/rag.py`:

```python
def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100):
    # Increase chunk_size for longer context
    # Increase overlap for better continuity
```

### Retrieval Settings

Adjust retrieval parameters in `llm_service.py`:

```python
# Retrieve more/fewer documents
context = get_dimension_context(dimension, survey_summary)  # Default: top_k=5

# Or customize:
context = service.retrieve_context(query, dimension, top_k=10)
```

## Knowledge Base Management

### Adding New Documents

1. Place documents in appropriate dimension folder:
   ```bash
   cp my_document.txt backend/Knowledge/privacy_compliance/
   ```

2. Re-ingest knowledge base:
   ```bash
   python -m app.rag --force
   ```

### Updating Documents

1. Edit documents in `Knowledge/` directory
2. Re-ingest with `--force` flag:
   ```bash
   python -m app.rag --force
   ```

### Adding New Dimensions

1. Create new folder in `Knowledge/`:
   ```bash
   mkdir backend/Knowledge/new_dimension
   ```

2. Add documents to folder

3. Update dimension mapping in `app/rag.py`:
   ```python
   dimension_mapping = {
       # ... existing mappings ...
       "new_dimension": "New Dimension Display Name"
   }
   ```

4. Ingest:
   ```bash
   python -m app.rag --force
   ```

## Troubleshooting

### Issue: "RAG service not enabled"

**Cause**: Dependencies not installed

**Solution**:
```bash
pip install chromadb sentence-transformers torch
```

### Issue: "No context retrieved"

**Causes**:
1. Knowledge base not ingested
2. Empty knowledge base
3. Query doesn't match any documents

**Solutions**:
1. Run ingestion: `python -m app.rag`
2. Check `Knowledge/` directory has files
3. Verify with test: `python test_rag.py`

### Issue: "Out of memory during ingestion"

**Cause**: Large knowledge base or limited RAM

**Solutions**:
1. Use smaller embedding model
2. Reduce chunk size
3. Process dimensions individually
4. Increase system RAM

### Issue: Downloads fail in setup_knowledge.py

**Cause**: Network issues or unavailable URLs

**Solution**: Script uses fallback content automatically. Check logs:
```
[WARNING] Using fallback content for privacy_compliance
```

Fallback content provides comprehensive coverage of all dimensions.

## Performance Considerations

### Vector Store Size

- Typical size: 100-500 MB for full knowledge base
- Location: `backend/chroma_db/`
- Can be deleted and regenerated anytime

### Embedding Generation

- First run: 1-5 minutes (downloads model)
- Subsequent runs: < 1 minute
- Model cached in: `~/.cache/torch/sentence_transformers/`

### Query Performance

- Retrieval time: < 100ms per query
- Embedding generation: < 50ms
- Total overhead: ~150ms per report generation

## Best Practices

1. **Ingest Once**: Run ingestion after setup, not on every startup
2. **Version Control**: Exclude `chroma_db/` from git (add to `.gitignore`)
3. **Knowledge Updates**: Re-ingest monthly or when standards update
4. **Quality Control**: Review retrieved context in test reports
5. **Fallback Content**: Always maintain fallback content for critical dimensions

## API Reference

### RAGService Class

```python
from app.rag import RAGService

# Initialize service
service = RAGService(
    knowledge_base_dir="path/to/Knowledge",
    chroma_persist_dir="path/to/chroma_db",
    embedding_model="all-MiniLM-L6-v2"
)

# Ingest knowledge base
result = service.ingest_knowledge(force_reingest=False)

# Retrieve context
context = service.retrieve_context(
    query="query text",
    dimension="Dimension Name",
    top_k=3,
    include_maturity=True
)

# Get dimension context
context = service.get_dimension_context(
    dimension="Dimension Name",
    survey_summary="Optional summary"
)

# Get statistics
stats = service.get_stats()
```

### Convenience Functions

```python
from app.rag import (
    initialize_rag,
    retrieve_context,
    get_dimension_context,
    get_rag_stats
)

# Initialize and ingest
initialize_rag(force_reingest=False)

# Retrieve context
context = retrieve_context(query, dimension, top_k=3)

# Get dimension context
context = get_dimension_context(dimension, survey_summary)

# Get stats
stats = get_rag_stats()
```

## Files Created/Modified

### New Files
- `backend/setup_knowledge.py` - Knowledge base setup script
- `backend/app/rag.py` - RAG service implementation
- `backend/test_rag.py` - RAG test suite
- `backend/RAG_INTEGRATION.md` - This documentation

### Modified Files
- `backend/requirements.txt` - Added RAG dependencies
- `backend/app/llm_service.py` - Integrated RAG context retrieval
- `backend/app/prompts/dimension_prompts.py` - Added maturity assessment section
- `backend/app/prompts/overall_summary_prompts.py` - Added enterprise maturity section

### Generated Directories
- `backend/Knowledge/` - Knowledge base documents (created by setup_knowledge.py)
- `backend/chroma_db/` - ChromaDB vector store (created by rag.py)

## Quick Start Checklist

- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Download knowledge base: `python setup_knowledge.py`
- [ ] Ingest into vector store: `python -m app.rag`
- [ ] Run tests: `python test_rag.py`
- [ ] Add to .gitignore: `chroma_db/`, `Knowledge/`
- [ ] Restart application to use RAG-enhanced reports

## Support

For issues or questions:

1. Check this documentation
2. Run test suite: `python test_rag.py`
3. Check logs for detailed error messages
4. Review ChromaDB documentation: https://docs.trychroma.com/
