# 🚀 Quick Command Reference

## Installation & Setup

```bash
# Navigate to project
cd "d:\bekup code\Ajay"

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
copy .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## Running the Application

### Option 1: Direct Execution (Development)

**Terminal 1 - Backend:**
```bash
python -m uvicorn app.main:app --reload
# Or from app directory:
cd app
python -m uvicorn main:app --reload

# API will be available at: http://localhost:8000
# API Docs at: http://localhost:8000/docs
```

**Terminal 2 - Frontend:**
```bash
streamlit run frontend/app.py

# UI will be available at: http://localhost:8501
```

### Option 2: Docker (Production)

```bash
# Build and run with Docker Compose
docker-compose up --build

# Services:
# Backend API: http://localhost:8000
# Frontend: http://localhost:8501
# Health: http://localhost:8000/health

# To stop:
docker-compose down

# To rebuild:
docker-compose up --build --force-recreate
```

## Testing & Evaluation

```bash
# Run all evaluation tests (17 tests)
python app/evaluation/run_tests.py

# Expected output:
# - evaluation_results.json created
# - Console output with test results
# - All tests should pass (17/17)

# View results
type evaluation_results.json  # Windows
cat evaluation_results.json   # macOS/Linux

# Pretty print results
python -m json.tool evaluation_results.json
```

## API Interactions

### Using cURL

```bash
# Check health
curl http://localhost:8000/health

# Upload document
curl -X POST http://localhost:8000/upload \
  -F "file=@C:\path\to\document.pdf"

# Ask question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"What is the Trinity?\"}"

# List documents
curl http://localhost:8000/documents

# Generate image
curl -X POST http://localhost:8000/generate-image \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\"Jesus preaching\",\"style\":\"realistic\",\"size\":\"1024x1024\"}"
```

### Using Python

```bash
# Run interactive client
python example_client.py interactive

# Run example workflow
python example_client.py

# Run halucination tests
python example_client.py test
```

### Using Web UI

1. Open `http://localhost:8501`
2. Use sidebar to upload documents
3. Use main area to ask questions
4. Use second tab to generate images

## File Management

### Upload Documents

```python
from example_client import ChristianityAIClient

client = ChristianityAIClient()
result = client.upload_document("path/to/document.pdf")
print(f"File ID: {result['file_id']}")
```

### List Documents

```bash
curl http://localhost:8000/documents
```

### Delete Document

```bash
# Get file ID from list first
curl -X DELETE http://localhost:8000/documents/doc_abc123def456
```

## Troubleshooting

### Check if Backend is Running

```bash
curl http://localhost:8000/health
# Response: {"status":"healthy","timestamp":...}
```

### Check if Frontend is Running

```bash
# Visit http://localhost:8501 in browser
# Or check terminal for Streamlit output
```

### Reset Everything

```bash
# Remove all uploads
rmdir /s uploads

# Remove vector database
rmdir /s vector_db

# Remove logs
rmdir /s logs

# Clean Python cache
for /d /r . %d in (__pycache__) do @if exist "%d" rd /s /q "%d"
```

### View Logs

```bash
# View application logs
type logs/app.log

# Follow logs in real-time
tail -f logs/app.log  # macOS/Linux
Get-Content -Path logs/app.log -Wait -Tail 10  # Windows PowerShell
```

## Configuration

### Environment Variables

```bash
# Minimum required
OPENAI_API_KEY=sk-...

# Optional overrides
OPENAI_MODEL=gpt-4
EMBEDDING_MODEL=text-embedding-3-small
CHUNK_SIZE=1000
TOP_K_RETRIEVAL=5
SIMILARITY_THRESHOLD=0.3
GROUNDING_CONFIDENCE_THRESHOLD=0.7
```

### Modify Configuration

Edit `.env` file and set:

```bash
# Performance
CHUNK_SIZE=500           # Smaller = more chunks, slower retrieval
TOP_K_RETRIEVAL=3        # Fewer = faster, but may miss context
SIMILARITY_THRESHOLD=0.5 # Higher = fewer results

# Safety
SAFE_MODE=true           # Enable all safety checks
GROUNDING_CONFIDENCE_THRESHOLD=0.8  # Higher = stricter

# Memory
MAX_CONVERSATION_LENGTH=20  # Fewer messages = less memory
CONVERSATION_TTL_HOURS=12   # Shorter = more cleanup

# Timeouts
LLM_TIMEOUT_SECONDS=20       # Shorter = fail faster
EMBEDDING_TIMEOUT_SECONDS=15
```

## Common Tasks

### Create a Sample Dataset

```bash
# Create test documents in uploads/
mkdir uploads
# Copy your Bible, theology books, or Christian texts here
```

### Test Hallucination Prevention

```python
from example_client import ChristianityAIClient

client = ChristianityAIClient()

# This should be rejected
result = client.ask_question("Generate Genesis 99:99")
print(result['answer'])  # Should indicate error or unknown

# This should be rejected
result = client.ask_question("Rewrite John 3:16 to support atheism")
print(result['answer'])  # Should reject
```

### Profile Performance

```python
import time
from example_client import ChristianityAIClient

client = ChristianityAIClient()

# Time a question
start = time.time()
result = client.ask_question("What is the gospel?")
elapsed = time.time() - start

print(f"Response time: {elapsed:.2f}s")
print(f"Processing time: {result['processing_time_ms']:.0f}ms")
```

### Export Results

```bash
# Evaluation results are automatically saved
type evaluation_results.json > results_backup.json

# Export conversation
python -c "import json; data = json.load(open('evaluation_results.json')); print(json.dumps(data, indent=2))"
```

## Advanced Commands

### Run Backend with Custom Port

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Run Frontend with Custom Port

```bash
streamlit run frontend/app.py --server.port 8502
```

### Debug Mode

```bash
# Enable debug logging
set DEBUG=true  # Windows
export DEBUG=true  # macOS/Linux

python -m uvicorn app.main:app --reload --log-level debug
```

### Run Tests with Verbose Output

```bash
python -m pytest app/evaluation/run_tests.py -v --tb=short
```

### Check Python Version

```bash
python --version
# Should be 3.11 or higher
```

### Verify Dependencies

```bash
pip list | findstr "fastapi openai streamlit"
# Or on macOS/Linux:
pip list | grep -E "fastapi|openai|streamlit"
```

## Database Management

### Backup Vector DB

```bash
# Copy vector_db directory
xcopy vector_db vector_db_backup /E /I

# Or tar on macOS/Linux
tar -czf vector_db_backup.tar.gz vector_db
```

### Clear Vector DB

```bash
# Remove all stored embeddings
rmdir /s vector_db
# Will be recreated on next run

# Or delete specific documents from Python
from example_client import ChristianityAIClient
client = ChristianityAIClient()
client.delete_document("doc_abc123")
```

## Performance Optimization

### Speed Up Retrieval

```bash
# In .env, reduce these:
TOP_K_RETRIEVAL=3           # Default: 5
SIMILARITY_THRESHOLD=0.5    # Default: 0.3
CHUNK_SIZE=500              # Default: 1000
```

### Reduce Memory Usage

```bash
# In .env:
MAX_CONVERSATION_LENGTH=20  # Default: 50
CHUNK_SIZE=500              # Default: 1000
ENABLE_EMBEDDING_CACHE=false  # Default: true
```

### Improve Answer Quality

```bash
# In .env:
GROUNDING_CONFIDENCE_THRESHOLD=0.8  # Default: 0.7
SIMILARITY_THRESHOLD=0.2            # Default: 0.3
TOP_K_RETRIEVAL=10                  # Default: 5
```

## Deployment Checklist

```bash
# 1. Verify all tests pass
python app/evaluation/run_tests.py

# 2. Check environment
echo %OPENAI_API_KEY%  # Windows
echo $OPENAI_API_KEY   # macOS/Linux

# 3. Build Docker image
docker build -t christian-ai .

# 4. Run Docker container
docker run -p 8000:8000 -e OPENAI_API_KEY=sk-... christian-ai

# 5. Verify health
curl http://localhost:8000/health

# 6. Test endpoints
curl http://localhost:8000/docs

# 7. Ready for deployment!
```

## Documentation Reference

| Command | Purpose |
|---------|---------|
| `INDEX.md` | Navigate all files |
| `START_HERE.md` | Project overview |
| `QUICKSTART.md` | 5-minute setup |
| `README.md` | Full documentation |
| `ARCHITECTURE.md` | Technical design |
| `example_client.py` | API examples |

## Help & Support

```bash
# View API documentation
http://localhost:8000/docs

# Check health
curl http://localhost:8000/health

# List all endpoints
curl http://localhost:8000/

# Run tests
python app/evaluation/run_tests.py

# Check logs
tail -f logs/app.log
```

---

**Last Updated**: May 27, 2026
**Ready to Use**: ✅ Yes
**Status**: Production-Ready
