# Christianity AI Assistant

An AI-powered Christianity Assistant built with **FastAPI**, **Streamlit**, **Google Gemini**, and **ChromaDB**.

The system allows users to upload Christian documents (Bible PDFs, study guides, theological resources, sermons, commentaries, etc.), ask grounded questions using Retrieval-Augmented Generation (RAG), maintain conversational context through memory-aware query rewriting, and generate Christian-themed images.

---

## Features

### 📖 Document Upload & Processing

* Upload PDF, DOCX, and TXT documents
* Automatic text extraction
* Intelligent document chunking
* Vector embedding generation
* ChromaDB vector storage
* Multi-document support

### 🔍 Retrieval-Augmented Generation (RAG)

* Semantic document search
* Context-aware question answering
* Source citations
* Similarity-based retrieval
* Hallucination reduction through grounded context

### 🧠 Conversation Memory

* Multi-turn conversations
* Context preservation
* Follow-up question support
* Query rewriting for pronoun resolution

Example:

**User:** Who was Noah?

**User:** How many sons did he have?

**Assistant:** Noah had three sons: Shem, Ham, and Japheth.

### ✝️ Christian AI Assistant

* Scripture-focused responses
* Grounded answers from uploaded documents
* Source-backed theological explanations
* Safety moderation

### 🎨 Image Generation

* Christian-themed image generation
* Multiple image styles
* Safety validation
* Gemini-powered image generation

---

# Architecture

```text
┌────────────────────────────────────────────┐
│             Streamlit Frontend             │
└─────────────────┬──────────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────┐
│              FastAPI Backend               │
├────────────────────────────────────────────┤
│                                            │
│  ┌──────────────────────────────────────┐  │
│  │           RAG System                 │  │
│  │                                      │  │
│  │ • Chunking                           │  │
│  │ • Embeddings                         │  │
│  │ • ChromaDB                           │  │
│  │ • Semantic Retrieval                 │  │
│  └──────────────────────────────────────┘  │
│                                            │
│  ┌──────────────────────────────────────┐  │
│  │         Gemini Services              │  │
│  │                                      │  │
│  │ • Question Answering                 │  │
│  │ • Query Rewriting                    │  │
│  │ • Conversation Memory                │  │
│  │ • Image Generation                   │  │
│  └──────────────────────────────────────┘  │
│                                            │
└────────────────────────────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────┐
│              Data Layer                    │
├────────────────────────────────────────────┤
│ ChromaDB • Uploaded Files • Memory Cache   │
└────────────────────────────────────────────┘
```

---

# Tech Stack

## Backend

* FastAPI
* Python 3.10.11

## Frontend

* Streamlit

## LLM

* Google Gemini

## Vector Database

* ChromaDB

## Embeddings

* Sentence Transformers

## Document Processing

* PyPDF2
* python-docx

## Deployment

* Docker
* Docker Compose

---

# Project Structure

```text
Christianity-AI-Assistant/

├── app/
│   ├── main.py
│   ├── config.py
│   │
│   ├── models/
│   ├── rag/
│   ├── services/
│   ├── utils/
│   └── evaluation/
│
├── frontend/
│   └── app.py
│
├── tests/
│
├── uploads/
├── vector_db/
├── logs/
│
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
└── ARCHITECTURE.md
```

---

# Prerequisites

## Python Version

Developed and tested using:

```text
Python 3.10.11
```

Recommended:

```text
Python 3.10.x
```

---

# Installation

## 1. Clone Repository

```bash
git clone https://github.com/<your-username>/Christianity-AI-Assistant.git

cd Christianity-AI-Assistant
```

---

## 2. Create Virtual Environment

### Windows

```bash
python -m venv venv
```

Activate:

```bash
venv\Scripts\activate
```

### Linux / Mac

```bash
python3 -m venv venv

source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a file named:

```text
.env
```

Example:

```env
GEMINI_API_KEY=your_gemini_api_key

GEMINI_MODEL=models/gemini-2.5-flash

CHROMA_PERSIST_DIR=./vector_db

UPLOAD_DIR=./uploads

LOG_DIR=./logs

CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RETRIEVAL=5
SIMILARITY_THRESHOLD=0.3
```

Get Gemini API Key:

https://aistudio.google.com/app/apikey

---

# VS Code Setup

Press:

```text
Ctrl + Shift + P
```

Search:

```text
Python: Select Interpreter
```

Choose:

```text
./venv/Scripts/python.exe
```

Verify:

```bash
python --version
```

Expected:

```text
Python 3.10.11
```

---

# Running the Backend

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://localhost:8000
```

API Docs:

```text
http://localhost:8000/docs
```

---

# Running the Frontend

Open another terminal:

```bash
streamlit run frontend/app.py
```

Frontend:

```text
http://localhost:8501
```

---

# Docker Setup

Build and run:

```bash
docker-compose up --build
```

Services:

```text
Backend:  http://localhost:8000

Frontend: http://localhost:8501

Docs:     http://localhost:8000/docs
```

---

# How To Use

## Upload Documents

1. Open Streamlit UI
2. Upload PDF, DOCX, or TXT documents
3. Wait for indexing
4. Documents become searchable

---

## Ask Questions

Examples:

```text
Who was Noah?

What did Jesus teach about forgiveness?

Summarize the Book of Genesis.

What is the Trinity?
```

### Follow-up Questions

```text
Who was Noah?

How many sons did he have?

What were their names?
```

The assistant automatically uses conversation memory and query rewriting to preserve context.

---

## Generate Images

Examples:

```text
Jesus walking on water

Noah's Ark during sunset

The Sermon on the Mount

The Last Supper in realistic style
```

---

# Screenshots

Add screenshots here after deployment.

```text
docs/screenshots/home.png

docs/screenshots/upload-document.png

docs/screenshots/question-answering.png

docs/screenshots/conversation-memory.png

docs/screenshots/image-generation.png
```

---

# Troubleshooting

## ChromaDB Batch Size Error

Example:

```text
Batch size exceeds maximum batch size
```

Solution:

Reduce ingestion batch size in:

```text
app/rag/rag_system.py
```

---

## Gemini Quota Error

Example:

```text
429 Quota exceeded
```

Solutions:

* Wait for quota reset
* Switch Gemini model
* Use another API key

---

## Missing PyPDF2

```bash
pip install PyPDF2
```

---

## Streamlit Compatibility Errors

Upgrade Streamlit:

```bash
pip install --upgrade streamlit
```

---

# Future Improvements

* Multi-model support
* Hugging Face LLM integration
* Hybrid Search (Vector + BM25)
* Persistent conversation storage
* Authentication system
* Cloud deployment
* Multi-language support
* Denomination-specific modes

---

# Author

**Ajay Tingare**

Software Engineer | AI Engineer

GitHub: https://github.com/ajaytingare

---

# License

This project is intended for educational, research, and portfolio purposes.
