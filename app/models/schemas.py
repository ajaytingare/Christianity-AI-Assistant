from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class DocumentChunk(BaseModel):
    """Represents a chunk of text from a document."""
    id: str
    content: str
    source_file: str
    page_number: Optional[int] = None
    metadata: dict = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    chunk_index: int


class Document(BaseModel):
    """Represents an uploaded document."""
    id: str
    filename: str
    file_type: str
    upload_date: datetime
    total_chunks: int
    status: str


class Question(BaseModel):
    """Request model for asking questions."""
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    similarity_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    use_citation: bool = Field(default=True)
    conversation_id: Optional[str] = None


class RetrievedChunk(BaseModel):
    """Represents a retrieved chunk with relevance score."""
    content: str
    source_file: str
    page_number: Optional[int] = None
    relevance_score: float
    chunk_index: int


class AnswerResponse(BaseModel):
    """Response model for questions."""
    answer: str
    confidence_score: float
    retrieved_chunks: List[RetrievedChunk]
    citations: List[str]
    is_grounded: bool
    processing_time_ms: float
    model_used: str


class ImageGenerationRequest(BaseModel):
    """Request model for image generation."""
    prompt: str = Field(..., min_length=10, max_length=1000)
    style: str = Field(default="realistic", regex="^(realistic|artistic|symbolic|abstract)$")
    size: str = Field(default="1024x1024", regex="^(512x512|1024x1024|1536x1536)$")


class ImageGenerationResponse(BaseModel):
    """Response model for image generation."""
    image_url: str
    prompt_used: str
    moderation_passed: bool
    processing_time_ms: float


class ConversationMessage(BaseModel):
    """Represents a message in a conversation."""
    role: str
    content: str
    timestamp: datetime
    metadata: dict = Field(default_factory=dict)


class ConversationContext(BaseModel):
    """Conversation memory context."""
    conversation_id: str
    messages: List[ConversationMessage] = Field(default_factory=list)
    created_at: datetime
    last_updated: datetime
    document_ids: List[str] = Field(default_factory=list)


class EvaluationMetrics(BaseModel):
    """Metrics for evaluation."""
    question: str
    expected_answer: Optional[str]
    generated_answer: str
    groundedness_score: float
    relevance_score: float
    hallucination_score: float
    retrieval_accuracy: float
    passed: bool


class SafetyCheckResult(BaseModel):
    """Result of safety/moderation check."""
    is_safe: bool
    flags: List[str] = Field(default_factory=list)
    reason: Optional[str] = None
    confidence: float
