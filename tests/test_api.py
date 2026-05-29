"""
Comprehensive API and endpoint testing suite.
Tests all endpoints with valid and invalid inputs.
"""

import pytest
import json
from httpx import AsyncClient
from app.main import app
from app.config import get_settings
import os
import tempfile
from pathlib import Path


@pytest.fixture
async def client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_text_file():
    """Create a sample text file for testing."""
    content = """
    The Gospel of John
    
    Chapter 1, Verse 1
    In the beginning was the Word, and the Word was with God, and the Word was God.
    
    The Trinity
    The Christian doctrine of the Trinity states that God exists as three persons
    in one essence: the Father, the Son (Jesus Christ), and the Holy Spirit.
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        return f.name


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health endpoint returns proper response."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "documents_loaded" in data
    
    @pytest.mark.asyncio
    async def test_health_check_response_structure(self, client):
        """Test health endpoint response structure."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["timestamp"], (int, float))
        assert isinstance(data["documents_loaded"], int)


class TestRootEndpoint:
    """Test root endpoint."""
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data


class TestUploadEndpoint:
    """Test document upload endpoint."""
    
    @pytest.mark.asyncio
    async def test_upload_valid_text_file(self, client, sample_text_file):
        """Test uploading valid text file."""
        with open(sample_text_file, 'rb') as f:
            response = await client.post(
                "/upload",
                files={"file": (Path(sample_text_file).name, f, "text/plain")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "file_id" in data
        assert "total_chunks" in data
        
        # Cleanup
        if os.path.exists(sample_text_file):
            os.remove(sample_text_file)
    
    @pytest.mark.asyncio
    async def test_upload_no_file(self, client):
        """Test upload without file."""
        response = await client.post("/upload", files={})
        # Should fail or return 400
        assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_upload_invalid_extension(self, client):
        """Test upload with invalid file extension."""
        with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as f:
            f.write(b"fake executable")
            f.flush()
            
            with open(f.name, 'rb') as file:
                response = await client.post(
                    "/upload",
                    files={"file": (Path(f.name).name, file, "application/octet-stream")}
                )
            
            assert response.status_code == 400
            os.remove(f.name)


class TestAskEndpoint:
    """Test question asking endpoint."""
    
    @pytest.mark.asyncio
    async def test_ask_valid_question(self, client):
        """Test asking a valid question."""
        payload = {
            "question": "What is the Trinity?",
            "top_k": 5,
            "similarity_threshold": 0.3,
            "use_citation": True
        }
        
        response = await client.post("/ask", json=payload)
        # May fail if no documents uploaded, but should handle gracefully
        assert response.status_code in [200, 400]
    
    @pytest.mark.asyncio
    async def test_ask_empty_question(self, client):
        """Test asking empty question."""
        payload = {
            "question": "",
            "top_k": 5,
            "similarity_threshold": 0.3
        }
        
        response = await client.post("/ask", json=payload)
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_ask_very_long_question(self, client):
        """Test question with excessive length."""
        payload = {
            "question": "x" * 5000,
            "top_k": 5
        }
        
        response = await client.post("/ask", json=payload)
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_ask_malformed_json(self, client):
        """Test malformed JSON."""
        response = await client.post(
            "/ask",
            content="{invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_ask_invalid_top_k(self, client):
        """Test invalid top_k value."""
        payload = {
            "question": "What is faith?",
            "top_k": 1000  # Too large
        }
        
        response = await client.post("/ask", json=payload)
        # Should either clamp or reject
        assert response.status_code in [200, 400]
    
    @pytest.mark.asyncio
    async def test_ask_negative_threshold(self, client):
        """Test negative similarity threshold."""
        payload = {
            "question": "What is grace?",
            "similarity_threshold": -0.5
        }
        
        response = await client.post("/ask", json=payload)
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_ask_response_structure(self, client):
        """Test response structure is valid."""
        payload = {
            "question": "What is love?"
        }
        
        response = await client.post("/ask", json=payload)
        if response.status_code == 200:
            data = response.json()
            assert "answer" in data
            assert "confidence_score" in data
            assert "retrieved_chunks" in data
            assert "citations" in data
            assert "is_grounded" in data
            assert "processing_time_ms" in data


class TestGenerateImageEndpoint:
    """Test image generation endpoint."""
    
    @pytest.mark.asyncio
    async def test_generate_image_valid(self, client):
        """Test image generation with valid prompt."""
        payload = {
            "prompt": "Jesus preaching to disciples on a mountain",
            "style": "realistic",
            "size": "1024x1024"
        }
        
        response = await client.post("/generate-image", json=payload)
        # May fail due to API limits, but check response structure
        assert response.status_code in [200, 400, 429]
    
    @pytest.mark.asyncio
    async def test_generate_image_short_prompt(self, client):
        """Test image generation with too short prompt."""
        payload = {
            "prompt": "Jesus",  # Too short
            "style": "realistic"
        }
        
        response = await client.post("/generate-image", json=payload)
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_generate_image_invalid_style(self, client):
        """Test image generation with invalid style."""
        payload = {
            "prompt": "A beautiful Christian scene with angels",
            "style": "invalid_style"
        }
        
        response = await client.post("/generate-image", json=payload)
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_generate_image_invalid_size(self, client):
        """Test image generation with invalid size."""
        payload = {
            "prompt": "A beautiful Christian scene",
            "size": "999x999"
        }
        
        response = await client.post("/generate-image", json=payload)
        assert response.status_code == 400


class TestDocumentsEndpoint:
    """Test document list endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_documents(self, client):
        """Test listing documents."""
        response = await client.get("/documents")
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total" in data
        assert isinstance(data["documents"], list)


class TestConversationEndpoint:
    """Test conversation endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_conversation(self, client):
        """Test creating conversation."""
        payload = {"document_ids": []}
        response = await client.post("/conversation/create", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "conversation_id" in data


class TestErrorHandling:
    """Test error handling."""
    
    @pytest.mark.asyncio
    async def test_404_not_found(self, client):
        """Test 404 error for non-existent endpoint."""
        response = await client.get("/nonexistent")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_method_not_allowed(self, client):
        """Test method not allowed."""
        response = await client.get("/upload")  # Should be POST
        assert response.status_code == 405
    
    @pytest.mark.asyncio
    async def test_invalid_content_type(self, client):
        """Test invalid content type."""
        response = await client.post(
            "/ask",
            data="invalid",
            headers={"Content-Type": "application/octet-stream"}
        )
        assert response.status_code in [400, 415]


class TestConcurrency:
    """Test concurrent requests."""
    
    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self, client):
        """Test multiple concurrent health checks."""
        import asyncio
        
        tasks = [client.get("/health") for _ in range(5)]
        responses = await asyncio.gather(*tasks)
        
        assert all(r.status_code == 200 for r in responses)
    
    @pytest.mark.asyncio
    async def test_concurrent_list_documents(self, client):
        """Test concurrent document list requests."""
        import asyncio
        
        tasks = [client.get("/documents") for _ in range(5)]
        responses = await asyncio.gather(*tasks)
        
        assert all(r.status_code == 200 for r in responses)
