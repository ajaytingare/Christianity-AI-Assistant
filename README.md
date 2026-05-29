# Christianity AI Assistant - Production-Ready RAG System

## Overview

A sophisticated AI assistant that answers Christianity and theology questions with **strict hallucination prevention**, grounded responses, and safety moderation. Built with RAG (Retrieval Augmented Generation), this system ensures answers are always sourced from uploaded documents.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Interface (Streamlit)                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    FastAPI Backend                              │
├─────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────┐    │
│ │              API Layer (routes & endpoints)              │    │
│ └──────────────┬──────────────────────────┬────────────────┘    │
│                │                          │                     │
│  ┌─────────────▼──────────┐   ┌──────────▼──────────────┐       │
│  │   RAG System           │   │  Safety & Moderation    │       │
│  ├────────────────────────┤   ├─────────────────────────┤       │
│  │ • Embeddings           │   │ • Hallucination checks  │       │
│  │ • Vector Store (Chroma)│   │ • Prompt moderation     │       │
│  │ • Chunking             │   │ • Response filtering    │       │
│  │ • Retrieval            │   │ • Scripture validation  │       │
│  └────────────────────────┘   └─────────────────────────┘       │
│                │                          │                     │
│  ┌─────────────▼──────────┐   ┌──────────▼───────────────┐      │
│  │   LLM Service          │   │  Document Processor      │      │
│  ├────────────────────────┤   ├──────────────────────────┤      │
│  │ • OpenAI API           │   │ • PDF extraction         │      │
│  │ • Grounded generation  │   │ • Text cleaning          │      │
│  │ • Image generation     │   │ • Intelligent chunking   │      │
│  └────────────────────────┘   └──────────────────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                   Data Layer                                    │
├─────────────────────────────────────────────────────────────────┤
│ • ChromaDB (Vector DB)  • File Storage  • Conversation Memory   │
└─────────────────────────────────────────────────────────────────┘
```

## Tech Stack

- **Backend**: FastAPI 0.109.0
- **LLM**: OpenAI GPT-4
- **Embeddings**: OpenAI text-embedding-3-small
- **Vector DB**: ChromaDB
- **Document Processing**: PyPDF2, pymupdf, python-docx
- **Frontend**: Streamlit
- **Language**: Python 3.11+
- **Orchestration**: Docker & Docker Compose

## Key Features

### 1. **Hallucination Prevention**
- ✅ Grounded context retrieval from documents
- ✅ Answer validation against retrieved chunks
- ✅ Scripture reference verification
- ✅ Confidence scoring (0-1)
- ✅ Source citation enforcement
- ✅ Similarity threshold filtering

### 2. **Safety & Moderation**
- ✅ Prompt injection detection
- ✅ Adversarial prompt rejection
- ✅ Offensive content filtering
- ✅ Scripture hallucination detection
- ✅ Ideology injection prevention
- ✅ OpenAI moderation API integration

### 3. **RAG System**
- ✅ Intelligent text chunking with overlap
- ✅ OpenAI embeddings for semantic search
- ✅ ChromaDB for efficient vector storage
- ✅ Cosine similarity-based retrieval
- ✅ Multi-document support
- ✅ Chunk metadata preservation

### 4. **Conversation Memory**
- ✅ Persistent conversation context
- ✅ Message history management
- ✅ TTL-based cleanup
- ✅ Document association

### 5. **Evaluation System**
- ✅ Hallucination detection tests
- ✅ Adversarial prompt testing
- ✅ Edge case handling
- ✅ Answer grounding validation
- ✅ Scripture accuracy verification
- ✅ Comprehensive metrics reporting

## Installation

### Prerequisites
- Python 3.11+
- OpenAI API key
- Docker & Docker Compose (optional)

### Local Setup

```bash
# Clone repository
cd "d:\bekup code\Ajay"

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Quick Start

**Terminal 1 - Start Backend:**
```bash
cd app
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Start Frontend:**
```bash
streamlit run frontend/app.py
```

Access the app at: `http://localhost:8501`

### Docker Setup

```bash
# Build and run with Docker Compose
docker-compose up --build

# Backend: http://localhost:8000
# Frontend: http://localhost:8501
# API Docs: http://localhost:8000/docs
```

## API Documentation

### 1. Upload Document
```bash
POST /upload

Curl Example:
curl -X POST "http://localhost:8000/upload" \
  -F "file=@path/to/document.pdf"

Response:
{
  "success": true,
  "file_id": "doc_abc123def456",
  "filename": "document.pdf",
  "total_chunks": 45,
  "message": "Document uploaded and processed successfully"
}
```

### 2. Ask Question
```bash
POST /ask

Request Body:
{
  "question": "What is the Trinity?",
  "top_k": 5,
  "similarity_threshold": 0.3,
  "use_citation": true,
  "conversation_id": null
}

Response:
{
  "answer": "The Trinity refers to the Christian doctrine...",
  "confidence_score": 0.85,
  "retrieved_chunks": [
    {
      "content": "...",
      "source_file": "document.pdf",
      "relevance_score": 0.92,
      "chunk_index": 3
    }
  ],
  "citations": [
    "document.pdf (Relevance: 92%)"
  ],
  "is_grounded": true,
  "processing_time_ms": 1240.5,
  "model_used": "gpt-4"
}
```

### 3. Generate Image
```bash
POST /generate-image

Request Body:
{
  "prompt": "Jesus preaching on the mountain with disciples",
  "style": "realistic",
  "size": "1024x1024"
}

Response:
{
  "image_url": "https://oaidalleapiprodscus.blob.core.windows.net/...",
  "prompt_used": "Jesus preaching on the mountain...",
  "moderation_passed": true,
  "processing_time_ms": 3500.0
}
```

### 4. List Documents
```bash
GET /documents

Response:
{
  "documents": [
    {
      "file_id": "doc_abc123",
      "filename": "bible_passages.pdf",
      "file_type": "pdf",
      "total_chunks": 120
    }
  ],
  "total": 1
}
```

### 5. Create Conversation
```bash
POST /conversation/create

Response:
{
  "conversation_id": "conv_xyz789"
}
```

## Project Structure

```
project_root/
│
├── app/
│   ├── __init__.py
│   ├── config.py                 # Configuration & settings
│   ├── main.py                   # FastAPI application
│   │
│   ├── api/
│   │   └── __init__.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_processor.py  # PDF/TXT/DOCX extraction
│   │   ├── llm_service.py         # LLM + hallucination prevention
│   │   ├── conversation_memory.py # Memory management
│   │   └── image_generation.py    # Image generation
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py             # Pydantic models
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   └── rag_system.py          # RAG pipeline
│   │
│   ├── prompts/
│   │   └── __init__.py
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   └── helpers.py             # Utility functions
│   │
│   └── evaluation/
│       ├── __init__.py
│       ├── evaluator.py           # Evaluation engine
│       └── run_tests.py            # Test runner
│
├── frontend/
│   └── app.py                    # Streamlit UI
│
├── tests/
│   └── __init__.py
│
├── uploads/                      # Document storage
├── vector_db/                    # ChromaDB storage
├── logs/                         # Application logs
│
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables
├── .env.example                  # Example env file
├── Dockerfile                    # Docker image
├── docker-compose.yml            # Docker Compose config
├── README.md                     # This file
└── ARCHITECTURE.md               # Detailed architecture
```

## Hallucination Prevention Mechanisms

### 1. **Grounded Context Forcing**
- Only retrieves relevant document chunks
- Forces LLM to answer only from retrieved context
- System prompt explicitly forbids hallucinations

### 2. **Answer Validation**
```python
# Calculate grounding score
groundedness = avg(chunk_relevance_scores)

# Check scripture accuracy
is_scripture_valid = all(references_in_answer in context)

# Validate confidence
is_confident = groundedness >= threshold
```

### 3. **Scripture Reference Verification**
- Detects Bible verse citations in responses
- Validates against retrieved context
- Rejects invalid/hallucinated references

### 4. **Similarity Threshold**
- Default: 0.3 cosine similarity
- Configurable per query
- Filters low-relevance chunks

### 5. **Confidence Scoring**
- Range: 0.0 to 1.0
- Based on retrieval quality
- Influences final response

## Safety & Moderation

### Content Moderation
- OpenAI moderation API for all inputs/outputs
- Flags offensive, harmful, unethical content
- Blocks unsafe prompts before processing

### Adversarial Prompt Detection
- Pattern matching for common attacks
- Ideology injection prevention
- Jailbreak attempt blocking

### Scripture Hallucination Detection
- Validates Bible verse format
- Checks against known references
- Rejects impossible verses (e.g., Genesis 99:99)

## Evaluation & Testing

### Test Coverage

Run comprehensive evaluation:
```bash
python app/evaluation/run_tests.py
```

**Test Categories:**

1. **Hallucination Prevention** (4 tests)
   - Fake verse generation
   - Scripture rewriting attempts
   - Made-up theological claims
   - Ideology injection

2. **Adversarial Prompts** (4 tests)
   - Instruction bypass attempts
   - Prompt injection
   - Jailbreak attempts
   - Role confusion

3. **Edge Cases** (5 tests)
   - Empty questions
   - Very long questions
   - Special characters
   - Non-English text
   - URL handling

4. **Answer Grounding** (4 tests)
   - Well-grounded answers
   - Hallucinated references
   - Generic denials
   - Made-up scripture

**Output:**
```json
{
  "timestamp": "2026-05-27T18:30:00",
  "test_suites": {
    "hallucination_prevention": {"passed": 4, "failed": 0, "total": 4},
    "adversarial_prompts": {"passed": 4, "failed": 0, "total": 4},
    "edge_cases": {"passed": 5, "failed": 0, "total": 5},
    "answer_grounding": {"passed": 4, "failed": 0, "total": 4}
  },
  "overall": {
    "total_tests": 17,
    "passed": 17,
    "failed": 0,
    "success_rate": 100.0
  }
}
```

## Configuration

### Environment Variables (.env)

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4
EMBEDDING_MODEL=text-embedding-3-small
IMAGE_GENERATION_MODEL=dall-e-3

# RAG Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
SIMILARITY_THRESHOLD=0.3
TOP_K_RETRIEVAL=5

# Safety Settings
GROUNDING_CONFIDENCE_THRESHOLD=0.7
ENABLE_HALLUCINATION_CHECK=true
SAFE_MODE=true

# Advanced Options
ENABLE_EMBEDDING_CACHE=true
CONVERSATION_TTL_HOURS=24
MAX_CONVERSATION_LENGTH=50
```

## Performance Optimization

### Embedding Cache
- Stores computed embeddings for reuse
- Reduces API calls and cost
- TTL-based automatic cleanup

### Batch Processing
- Processes multiple document chunks in parallel
- Efficient API utilization
- Configurable batch sizes

### Async Operations
- Non-blocking document processing
- Concurrent API requests
- Responsive user interface

## Monitoring & Logging

### Structured Logging
- Request ID tracking
- Processing time metrics
- Error tracking and reporting

### Metrics Tracked
- Question processing time
- Retrieval quality scores
- Model inference time
- Cache hit rates
- Error rates

### Log Levels
- INFO: Normal operations
- WARNING: Potential issues
- ERROR: Failed operations

Access logs:
```bash
tail -f logs/app.log
```

## Security Considerations

### Input Validation
- File type validation
- Size limits (50MB default)
- Question length constraints

### API Security
- Rate limiting (100 calls/hour)
- Request ID tracking
- Timeout protection

### Environment Security
- API keys in .env (never in code)
- No credentials in logs
- Secure embeddings storage

## Troubleshooting

### Common Issues

**1. OpenAI API Rate Limit**
```
Error: Rate limit exceeded
Solution: Implement exponential backoff (already in code)
```

**2. ChromaDB Connection Error**
```
Error: Failed to connect to vector store
Solution: Check vector_db directory permissions
```

**3. Out of Memory**
```
Error: Memory allocation failed
Solution: Reduce CHUNK_SIZE or MAX_CONVERSATION_LENGTH
```

**4. Slow Retrieval**
```
Issue: Slow vector search
Solution: Check vector_db file size, consider pruning old documents
```

## Interview-Ready Highlights

### Engineering Excellence
- ✅ Production-grade architecture
- ✅ Comprehensive error handling
- ✅ Async/await for performance
- ✅ Type hints throughout
- ✅ Modular, reusable code

### AI Safety & Grounding
- ✅ Hallucination prevention pipeline
- ✅ Scripture accuracy validation
- ✅ Safety moderation layer
- ✅ Adversarial prompt detection
- ✅ Confidence scoring

### Scalability
- ✅ Docker containerization
- ✅ Async API endpoints
- ✅ Batch processing capability
- ✅ Vector DB optimization
- ✅ Configurable parameters

### Quality Assurance
- ✅ 17+ comprehensive tests
- ✅ Edge case handling
- ✅ Evaluation metrics
- ✅ Logging & monitoring
- ✅ Error recovery

## Future Enhancements

1. **Advanced Features**
   - Multi-language support
   - Theological debate mode
   - Commentary integration
   - Historical context

2. **Performance**
   - Distributed vector search
   - GPU-accelerated embeddings
   - Advanced caching strategies

3. **Safety**
   - Fine-tuned safety model
   - Denomination-specific guidelines
   - Controversial topic handling

4. **Analytics**
   - Usage statistics
   - Question classification
   - Popular topics tracking

## License

Proprietary - Interview Project

## Contact & Support

For issues or questions about the system architecture, see `ARCHITECTURE.md`.

---

**Built for:** AI Engineering Interview Assessment
**Status:** Production-Ready
**Last Updated:** May 27, 2026
