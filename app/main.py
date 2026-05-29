"""
FastAPI main application with all security and stability fixes.
"""

import logging
import time
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from app.config import get_settings, validate_startup_settings
from app.models.schemas import (
    Question, AnswerResponse, RetrievedChunk,
    ImageGenerationRequest, ImageGenerationResponse
)
from app.services.document_processor import DocumentProcessor
from app.rag.rag_system import RAGSystem
from app.services.llm_service import LLMService
from app.services.conversation_memory import ConversationMemory
from app.services.image_generation import ImageGenerationService
from app.utils.helpers import RequestLogger, IDGenerator, FileUtils, ValidationUtils
from app.utils.async_file_handler import save_upload_file_async
from app.utils.rate_limiter import get_rate_limiter
from app.utils.exception_handlers import (
    global_exception_handler, validation_exception_handler, request_middleware
)
import os
from pathlib import Path

logger = logging.getLogger(__name__)
settings = get_settings()

# Service instances (initialized at startup)
class AppState:
    """Centralized application state."""
    def __init__(self):
        self.processed_documents = {}
        self.rag_system: RAGSystem = None
        self.conversation_memory: ConversationMemory = None
        self.document_processor: DocumentProcessor = None
        self.llm_service: LLMService = None
        self.image_generation_service: ImageGenerationService = None
        self.rate_limiter = None


app_state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events with validation."""
    logger.info("🚀 Starting up application...")
    
    try:
        # Validate startup configuration
        startup_valid = await validate_startup_settings()
        if not startup_valid:
            raise RuntimeError("Startup configuration validation failed")
        
        logger.info("✅ Configuration validated")
        
        # Initialize RAG system
        app_state.rag_system = RAGSystem()
        await app_state.rag_system.initialize()
        logger.info("✅ RAG system initialized")
        
        # Initialize services
        app_state.conversation_memory = ConversationMemory()
        app_state.document_processor = DocumentProcessor()
        app_state.llm_service = LLMService()
        
        app_state.image_generation_service = ImageGenerationService()
        logger.info("✅ All services initialized")
        
        # Initialize rate limiter
        app_state.rate_limiter = get_rate_limiter(
            settings.RATE_LIMIT_CALLS,
            settings.RATE_LIMIT_PERIOD
        )
        logger.info("✅ Rate limiter initialized")
        
        logger.info("✅ Application startup complete")

        #
        print("="*20)
        print(
            "APP MEMORY:",
            id(app_state.conversation_memory)
        )
        print("="*20)
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        raise
    
    yield
    
    logger.info("🛑 Shutting down application...")
    # Add cleanup code here if needed
    logger.info("✅ Application shutdown complete")


# Create FastAPI app with enhanced configuration
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:3000", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    max_age=600,
)

# Add request tracking middleware
app.middleware("http")(request_middleware)

# Add exception handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


# ============ ENDPOINTS ============

@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint with service status."""
    try:
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": settings.API_VERSION,
            "documents_loaded": len(app_state.processed_documents),
            "services": {
                "rag": "initialized" if app_state.rag_system else "not initialized",
                "llm": "initialized" if app_state.llm_service else "not initialized",
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": time.time(),
        }


@app.get("/")
async def root() -> dict:
    """API information endpoint."""
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "operational",
        "endpoints": {
            "health": "GET /health",
            "upload": "POST /upload",
            "ask": "POST /ask",
            "generate_image": "POST /generate-image",
            "documents": "GET /documents",
            "docs": "GET /docs"
        }
    }


@app.post("/upload")
async def upload_document(request: Request, file: UploadFile = File(...)) -> dict:
    """Upload and process a document with security checks."""
    request_id = getattr(request.state, "request_id", IDGenerator.generate_request_id())
    start_time = time.time()
    
    try:
        # Rate limiting check
        client_ip = request.client.host if request.client else "unknown"
        if settings.ENABLE_RATE_LIMIT and not app_state.rate_limiter.is_allowed(client_ip):
            logger.warning(f"Rate limit exceeded for {client_ip}")
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        RequestLogger.log_request(request_id, "/upload", {"filename": file.filename})
        
        # Validation
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_ext = FileUtils.get_file_extension(file.filename)
        if not FileUtils.validate_filename(file.filename, settings.ALLOWED_EXTENSIONS):
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Generate safe file path
        file_id = FileUtils.generate_file_id(file.filename)
        # Sanitize filename to prevent path traversal
        safe_filename = Path(file.filename).name  # Get just the filename
        file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}_{safe_filename}")
        
        # Read file contents
        contents = await file.read()
        
        # Save file asynchronously (non-blocking)
        success, error_msg = await save_upload_file_async(
            file_path, contents, settings.MAX_FILE_SIZE_MB
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Validate document
        is_valid, error_msg = await app_state.document_processor.validate_document(file_path)
        if not is_valid:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Extract text
        text, metadata = await app_state.document_processor.extract_text(file_path, file_ext)
        
        if not text.strip():
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="Document is empty or unreadable")
        
        # Create chunks
        chunks = await app_state.document_processor.chunk_text(
            text, file_id, file.filename
        )
        
        if not chunks:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="Could not create chunks from document")
        
        # Ingest into RAG
        await app_state.rag_system.ingest_document(chunks)
        
        # Track document
        app_state.processed_documents[file_id] = {
            "filename": file.filename,
            "file_type": file_ext,
            "total_chunks": len(chunks),
            "upload_time": time.time(),
            "file_path": file_path,
            "metadata": metadata
        }
        
        processing_time_ms = (time.time() - start_time) * 1000
        RequestLogger.log_response(request_id, 200, processing_time_ms)
        
        logger.info(f"✅ Document uploaded: {file_id} with {len(chunks)} chunks")
        
        return {
            "success": True,
            "file_id": file_id,
            "filename": file.filename,
            "total_chunks": len(chunks),
            "message": "Document uploaded and processed successfully",
            "processing_time_ms": processing_time_ms
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading document: {e}", exc_info=True)
        RequestLogger.log_error(request_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document"
        )


@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: Request, question_request: Question) -> AnswerResponse:
    
    request_id = getattr(
        request.state,
        "request_id",
        IDGenerator.generate_request_id()
    )

    start_time = time.time()

    # Validate input
    is_valid, error_msg = ValidationUtils.validate_question(
        question_request.question
    )

    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Safety check
    is_safe, safety_msg = await app_state.llm_service.moderate_prompt(
        question_request.question
    )

    if not is_safe:
        raise HTTPException(
            status_code=400,
            detail="Prompt validation failed"
        )

    # --------------------------------------------------
    # Get conversation history BEFORE retrieval
    # --------------------------------------------------

    conversation_history = []

    if question_request.conversation_id:

        conversation_history = (
            app_state.conversation_memory.get_message_history(
                question_request.conversation_id,
                limit=10
            )
        )

    # --------------------------------------------------
    # Rewrite question using history
    # --------------------------------------------------

    rewritten_question = (
        await app_state.llm_service.rewrite_question(
            question_request.question,
            conversation_history
        )
    )

    print("\n" + "="*60)
    print("ORIGINAL :", question_request.question)
    print("REWRITTEN:", rewritten_question)
    print("HISTORY  :", conversation_history)
    print("="*60)

    # --------------------------------------------------
    # Save user message
    # --------------------------------------------------

    if question_request.conversation_id:

        app_state.conversation_memory.add_message(
            question_request.conversation_id,
            "user",
            question_request.question
        )

    # --------------------------------------------------
    # Retrieve context using rewritten question
    # --------------------------------------------------

    retrieved_chunks, embedding = (
        await app_state.rag_system.retrieve_context(
            rewritten_question,
            question_request.top_k,
            question_request.similarity_threshold
        )
    )

    # --------------------------------------------------
    # Generate answer
    # --------------------------------------------------

    if not retrieved_chunks:

        answer = (
            "I could not find relevant information "
            "in the uploaded documents."
        )

        confidence_score = 0.0
        is_grounded = False

    else:

        answer, confidence_score, is_grounded = (
            await app_state.llm_service.generate_answer(
                rewritten_question,
                retrieved_chunks,
                conversation_history
            )
        )

        # Save assistant reply

        if question_request.conversation_id:

            app_state.conversation_memory.add_message(
                question_request.conversation_id,
                "assistant",
                answer
            )

        # Safety check answer

        safety_check = (
            await app_state.llm_service.moderate_response(
                answer
            )
        )

        if not safety_check.is_safe:

            answer = (
                "Cannot provide answer due to "
                "safety concerns."
            )

            is_grounded = False

    # --------------------------------------------------
    # Citations
    # --------------------------------------------------

    citations = []

    if question_request.use_citation and retrieved_chunks:

        citations = [
            f"{chunk.source_file} "
            f"(Relevance: {chunk.relevance_score:.1%})"
            for chunk in retrieved_chunks[:3]
        ]

    processing_time_ms = (
        time.time() - start_time
    ) * 1000

    return AnswerResponse(
        answer=answer,
        confidence_score=confidence_score,
        retrieved_chunks=retrieved_chunks,
        citations=citations,
        is_grounded=is_grounded,
        processing_time_ms=processing_time_ms,
        model_used=settings.GEMINI_MODEL
    )


@app.post("/generate-image", response_model=ImageGenerationResponse)
async def generate_image(request: Request, image_request: ImageGenerationRequest):
    """Generate Christian-themed image."""
    request_id = getattr(request.state, "request_id", IDGenerator.generate_request_id())
    start_time = time.time()
    
    try:
        # Rate limiting
        client_ip = request.client.host if request.client else "unknown"
        if settings.ENABLE_RATE_LIMIT and not app_state.rate_limiter.is_allowed(client_ip):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        RequestLogger.log_request(request_id, "/generate-image", {
            "prompt_length": len(image_request.prompt)
        })
        
        # Generate image
        image_url, success = await app_state.image_generation_service.generate_image(
            image_request.prompt,
            image_request.size,
            image_request.style
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to generate image or prompt rejected")
        
        processing_time_ms = (time.time() - start_time) * 1000
        RequestLogger.log_response(request_id, 200, processing_time_ms)
        
        return ImageGenerationResponse(
            image_url=image_url,
            prompt_used=image_request.prompt,
            moderation_passed=True,
            processing_time_ms=processing_time_ms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating image: {e}", exc_info=True)
        RequestLogger.log_error(request_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate image"
        )


@app.get("/documents")
async def list_documents(request: Request) -> dict:
    """List all uploaded documents."""
    try:
        docs = [
            {
                "file_id": fid,
                "filename": doc["filename"],
                "file_type": doc["file_type"],
                "total_chunks": doc["total_chunks"],
                "uploaded_at": doc["upload_time"]
            }
            for fid, doc in app_state.processed_documents.items()
        ]
        return {"documents": docs, "total": len(docs)}
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to list documents")


@app.delete("/documents/{file_id}")
async def delete_document(request: Request, file_id: str) -> dict:
    """Delete a document."""
    try:
        if file_id not in app_state.processed_documents:
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc = app_state.processed_documents[file_id]
        
        # Clean up file
        if os.path.exists(doc["file_path"]):
            os.remove(doc["file_path"])
        
        # Remove from vector DB
        await app_state.rag_system.vector_store.delete_by_source(doc["filename"])
        
        # Remove from tracking
        del app_state.processed_documents[file_id]
        
        logger.info(f"✅ Deleted document: {file_id}")
        
        return {"message": "Document deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")


@app.post("/conversation/create")
async def create_conversation(request: Request) -> dict:
    """Create a new conversation."""
    try:
        print(
            "CREATE ENDPOINT MEMORY:",
            id(app_state.conversation_memory)
        )
        conv_id = app_state.conversation_memory.create_conversation()
        return {"conversation_id": conv_id}
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create conversation")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level=settings.LOG_LEVEL.lower()
    )
