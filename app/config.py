# from pydantic_settings import BaseSettings
from pydantic import BaseSettings
from pydantic import Field, validator
from functools import lru_cache
import os
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    API_TITLE: str = "Christianity AI Assistant"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # OpenAI Configuration
    # OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    # OPENAI_MODEL: str = Field(default="gpt-4", description="LLM model to use")
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    EMBEDDING_MODEL: str = Field(default="text-embedding-3-small", description="Embedding model")
    IMAGE_GENERATION_MODEL: str = Field(default="dall-e-3", description="Image generation model")
    
    # RAG Configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RETRIEVAL: int = 5
    SIMILARITY_THRESHOLD: float = 0.3
    
    # Vector DB Configuration
    CHROMA_PERSIST_DIR: str = "./vector_db"
    VECTOR_DB_TYPE: str = "chroma"
    
    # File Upload Configuration
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: set = {"pdf", "txt", "docx"}
    
    # Hallucination Prevention
    REQUIRE_SOURCE_CITATION: bool = True
    GROUNDING_CONFIDENCE_THRESHOLD: float = 0.7
    ENABLE_HALLUCINATION_CHECK: bool = True
    
    # Scripture/Religion Configuration
    ENABLE_SCRIPTURE_VALIDATION: bool = True
    DENOMINATION_AWARE: bool = True
    SAFE_MODE: bool = True
    
    # Conversation Memory
    CONVERSATION_TTL_HOURS: int = 24
    MAX_CONVERSATION_LENGTH: int = 50
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"
    
    # Rate Limiting
    ENABLE_RATE_LIMIT: bool = True
    RATE_LIMIT_CALLS: int = 100
    RATE_LIMIT_PERIOD: int = 3600
    
    # Performance
    ENABLE_EMBEDDING_CACHE: bool = True
    CACHE_TTL_HOURS: int = 24
    
    # Timeouts
    LLM_TIMEOUT_SECONDS: int = 30
    EMBEDDING_TIMEOUT_SECONDS: int = 20
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance with validation."""
    settings = Settings()
    
    # Validate critical settings
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_api_key_here":
        raise ValueError(
            "GEMINI_API_KEY environment variable is required and must be set to a valid key. "
            "Get your key from https://aistudio.google.com/app/apikey"
        )
    
    if not settings.GEMINI_MODEL:
        raise ValueError("GEMINI_MODEL configuration is missing")
    
    if settings.CHUNK_SIZE < 100:
        logger.warning(f"⚠️ CHUNK_SIZE is very small ({settings.CHUNK_SIZE}), may cause issues")
    
    if settings.CHUNK_SIZE > 10000:
        logger.warning(f"⚠️ CHUNK_SIZE is very large ({settings.CHUNK_SIZE}), may be inefficient")
    
    return settings


async def validate_startup_settings() -> bool:
    """Async validation of settings at startup."""
    settings = get_settings()
    
    # Validate directories can be created
    try:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        os.makedirs(settings.LOG_DIR, exist_ok=True)
        logger.info("✅ All required directories verified/created")
    except Exception as e:
        logger.error(f"❌ Failed to create required directories: {e}")
        return False
    
    # Validate GEMINI API key format
    if len(settings.GEMINI_API_KEY) < 20:
        logger.warning("⚠️ GEMINI_API_KEY seems too short")
    
    return True
