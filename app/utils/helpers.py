import logging
import json
import hashlib
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
import asyncio
from functools import wraps
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RequestLogger:
    """Structured logging for requests."""
    
    @staticmethod
    def log_request(request_id: str, endpoint: str, data: Dict[str, Any]):
        """Log incoming request."""
        logger.info(json.dumps({
            "event": "request",
            "request_id": request_id,
            "endpoint": endpoint,
            "timestamp": datetime.utcnow().isoformat(),
            "data_keys": list(data.keys())
        }))
    
    @staticmethod
    def log_response(request_id: str, status: int, processing_time_ms: float):
        """Log outgoing response."""
        logger.info(json.dumps({
            "event": "response",
            "request_id": request_id,
            "status": status,
            "processing_time_ms": processing_time_ms,
            "timestamp": datetime.utcnow().isoformat()
        }))
    
    @staticmethod
    def log_error(request_id: str, error: str, traceback: str = None):
        """Log error."""
        logger.error(json.dumps({
            "event": "error",
            "request_id": request_id,
            "error": error,
            "traceback": traceback,
            "timestamp": datetime.utcnow().isoformat()
        }))


class TextProcessing:
    """Text processing utilities."""
    
    @staticmethod
    def generate_chunks(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size]
            if chunk.strip():
                chunks.append(chunk)
        return chunks
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text."""
        text = text.strip()
        text = " ".join(text.split())
        return text
    
    @staticmethod
    def extract_sentences(text: str, max_sentences: int = 10) -> List[str]:
        """Extract first N sentences from text."""
        sentences = text.split(". ")
        return sentences[:max_sentences]
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 500) -> str:
        """Truncate text to max length."""
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text


class FileUtils:
    """File operation utilities."""
    
    @staticmethod
    def generate_file_id(filename: str) -> str:
        """Generate unique file ID."""
        timestamp = str(time.time()).encode()
        filename_bytes = filename.encode()
        hash_obj = hashlib.md5(timestamp + filename_bytes)
        return f"doc_{hash_obj.hexdigest()[:12]}"
    
    @staticmethod
    def validate_filename(filename: str, allowed_extensions: set) -> bool:
        """Validate file extension."""
        if not filename:
            return False
        ext = filename.rsplit(".", 1)[-1].lower()
        return ext in allowed_extensions
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Get file extension."""
        if "." not in filename:
            return ""
        return filename.rsplit(".", 1)[-1].lower()


class ValidationUtils:
    """Validation utilities."""
    
    @staticmethod
    def validate_question(question: str, min_length: int = 3, max_length: int = 2000) -> tuple[bool, Optional[str]]:
        """Validate question input."""
        if not question or not isinstance(question, str):
            return False, "Question must be a non-empty string"
        
        question = question.strip()
        if len(question) < min_length:
            return False, f"Question too short (minimum {min_length} characters)"
        
        if len(question) > max_length:
            return False, f"Question too long (maximum {max_length} characters)"
        
        return True, None
    
    @staticmethod
    def sanitize_prompt(prompt: str) -> str:
        """Sanitize prompt to prevent injection attacks."""
        dangerous_patterns = [
            "sql", "bash", "shell", "system", "exec", "eval",
            "import", "open", "read", "write"
        ]
        
        prompt_lower = prompt.lower()
        for pattern in dangerous_patterns:
            if pattern in prompt_lower:
                logger.warning(f"Potentially dangerous pattern detected: {pattern}")
        
        return prompt


class IDGenerator:
    """Generate unique IDs."""
    
    @staticmethod
    def generate_request_id() -> str:
        """Generate unique request ID."""
        return f"req_{uuid.uuid4().hex[:12]}"
    
    @staticmethod
    def generate_conversation_id() -> str:
        """Generate unique conversation ID."""
        return f"conv_{uuid.uuid4().hex[:12]}"
    
    @staticmethod
    def generate_chunk_id() -> str:
        """Generate unique chunk ID."""
        return f"chunk_{uuid.uuid4().hex[:12]}"


def timer_decorator(func):
    """Decorator to measure function execution time."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(f"{func.__name__} took {elapsed_ms:.2f}ms")
        return result
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(f"{func.__name__} took {elapsed_ms:.2f}ms")
        return result
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper
