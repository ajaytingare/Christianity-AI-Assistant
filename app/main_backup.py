import logging
import time
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.config import get_settings
from app.models.schemas import (
    Question, AnswerResponse, RetrievedChunk, Document,
    ImageGenerationRequest, ImageGenerationResponse
)
from app.services.document_processor import DocumentProcessor
from app.rag.rag_system import RAGSystem
from app.services.llm_service import LLMService
from app.services.conversation_memory import ConversationMemory
from app.services.image_generation import ImageGenerationService
from app.utils.helpers import RequestLogger, IDGenerator, FileUtils, ValidationUtils
import os
from pathlib import Path

logger = logging.getLogger(__name__)
settings = get_settings()

processed_documents = {}
rag_system = None
conversation_memory = None
document_processor = None
llm_service = None
image_generation_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global rag_system, conversation_memory, document_processor, llm_service, image_generation_service
    
    logger.info("Starting up application...")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    
    rag_system = RAGSystem()
    await rag_system.initialize()
    
    conversation_memory = ConversationMemory()
    document_processor = DocumentProcessor()
    llm_service = LLMService()
    image_generation_service = ImageGenerationService()
    
    logger.info("Application startup complete")
    yield
    
    logger.info("Shutting down application...")


app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "documents_loaded": len(processed_documents)
    }


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document."""
    request_id = IDGenerator.generate_request_id()
    start_time = time.time()
    
    try:
        RequestLogger.log_request(request_id, "/upload", {"filename": file.filename})
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_ext = FileUtils.get_file_extension(file.filename)
        if not FileUtils.validate_filename(file.filename, settings.ALLOWED_EXTENSIONS):
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
            )
        
        file_id = FileUtils.generate_file_id(file.filename)
        file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}_{file.filename}")
        
        with open(file_path, "wb") as f:
            contents = await file.read()
            f.write(contents)
        
        is_valid, error_msg = await document_processor.validate_document(file_path)
        if not is_valid:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail=error_msg)
        
        text, metadata = await document_processor.extract_text(file_path, file_ext)
        
        if not text.strip():
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="Document is empty or unreadable")
        
        chunks = await document_processor.chunk_text(text, file_id, file.filename)
        
        await rag_system.ingest_document(chunks)
        
        processed_documents[file_id] = {
            "filename": file.filename,
            "file_type": file_ext,
            "total_chunks": len(chunks),
            "upload_time": time.time(),
            "file_path": file_path
        }
        
        processing_time_ms = (time.time() - start_time) * 1000
        RequestLogger.log_response(request_id, 200, processing_time_ms)
        
        return {
            "success": True,
            "file_id": file_id,
            "filename": file.filename,
            "total_chunks": len(chunks),
            "message": "Document uploaded and processed successfully"
        }
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        RequestLogger.log_error(request_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask", response_model=AnswerResponse)
async def ask_question(question_request: Question):
    """Ask a question about uploaded documents."""
    request_id = IDGenerator.generate_request_id()
    start_time = time.time()
    
    try:
        RequestLogger.log_request(request_id, "/ask", {"question": question_request.question})
        
        is_valid, error_msg = ValidationUtils.validate_question(question_request.question)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        is_safe, safety_msg = await llm_service.moderate_prompt(question_request.question)
        if not is_safe:
            raise HTTPException(status_code=400, detail=f"Prompt validation failed: {safety_msg}")
        
        retrieved_chunks, _ = await rag_system.retrieve_context(
            question_request.question,
            top_k=question_request.top_k,
            threshold=question_request.similarity_threshold
        )
        
        if not retrieved_chunks:
            answer = "I could not find relevant information in the uploaded documents to answer this question."
            confidence_score = 0.0
            is_grounded = False
        else:
            answer, confidence_score, is_grounded = await llm_service.generate_answer(
                question_request.question,
                retrieved_chunks
            )
            
            safety_check = await llm_service.moderate_response(answer)
            if not safety_check.is_safe:
                answer = "I cannot provide an answer to this question. It may violate content policies."
                is_grounded = False
        
        citations = []
        if question_request.use_citation and retrieved_chunks:
            citations = [
                f"{chunk.source_file} (Relevance: {chunk.relevance_score:.1%})"
                for chunk in retrieved_chunks[:3]
            ]
        
        processing_time_ms = (time.time() - start_time) * 1000
        RequestLogger.log_response(request_id, 200, processing_time_ms)
        
        return AnswerResponse(
            answer=answer,
            confidence_score=confidence_score,
            retrieved_chunks=retrieved_chunks,
            citations=citations,
            is_grounded=is_grounded,
            processing_time_ms=processing_time_ms,
            model_used=settings.OPENAI_MODEL
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error asking question: {e}")
        RequestLogger.log_error(request_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-image", response_model=ImageGenerationResponse)
async def generate_image(request: ImageGenerationRequest):
    """Generate Christian-themed image."""
    request_id = IDGenerator.generate_request_id()
    start_time = time.time()
    
    try:
        RequestLogger.log_request(request_id, "/generate-image", {"prompt_length": len(request.prompt)})
        
        image_url, success = await image_generation_service.generate_image(
            request.prompt,
            request.size,
            request.style
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to generate image or prompt rejected")
        
        processing_time_ms = (time.time() - start_time) * 1000
        RequestLogger.log_response(request_id, 200, processing_time_ms)
        
        return ImageGenerationResponse(
            image_url=image_url,
            prompt_used=request.prompt,
            moderation_passed=True,
            processing_time_ms=processing_time_ms
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        RequestLogger.log_error(request_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/conversation/create")
async def create_conversation(document_ids: list = None):
    """Create a new conversation context."""
    conv_id = conversation_memory.create_conversation(document_ids)
    return {"conversation_id": conv_id}


@app.get("/documents")
async def list_documents():
    """List all uploaded documents."""
    docs = [
        {
            "file_id": fid,
            "filename": doc["filename"],
            "file_type": doc["file_type"],
            "total_chunks": doc["total_chunks"]
        }
        for fid, doc in processed_documents.items()
    ]
    return {"documents": docs, "total": len(docs)}


@app.delete("/documents/{file_id}")
async def delete_document(file_id: str):
    """Delete a document."""
    if file_id not in processed_documents:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = processed_documents[file_id]
    
    if os.path.exists(doc["file_path"]):
        os.remove(doc["file_path"])
    
    await rag_system.vector_store.delete_by_source(doc["filename"])
    del processed_documents[file_id]
    
    return {"message": "Document deleted successfully"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "docs": "/docs",
        "endpoints": {
            "health": "GET /health",
            "upload": "POST /upload",
            "ask": "POST /ask",
            "generate_image": "POST /generate-image",
            "documents": "GET /documents",
            "create_conversation": "POST /conversation/create"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
