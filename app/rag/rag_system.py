import logging
from typing import List, Optional, Tuple
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
import chromadb
# from chromadb.config import Settings as ChromaSettings
from app.models.schemas import DocumentChunk, RetrievedChunk
from app.config import get_settings
import asyncio

logger = logging.getLogger(__name__)
settings = get_settings()


class VectorStore:
    """Vector database management using ChromaDB."""
    
    def __init__(self, persist_dir: str = None):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        # self.client = chromadb.Client(
        #     ChromaSettings(
        #         chroma_db_impl="duckdb+parquet",
        #         persist_directory=self.persist_dir,
        #         anonymized_telemetry=False
        #     )
        # )
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR
        )
        self.collection = None
    
    async def initialize(self):
        """Initialize or get collection."""
        try:
            self.collection = self.client.get_or_create_collection(
                name="christian_documents",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Vector store initialized")
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            raise
    
    async def add_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]):
        """Add document chunks with embeddings to vector store."""
        if not self.collection:
            await self.initialize()
        
        try:
            batch_size = 1000

            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i + batch_size]
                batch_embeddings = embeddings[i:i + batch_size]

                self.collection.add(
                    ids=[chunk.id for chunk in batch_chunks],
                    embeddings=batch_embeddings,
                    documents=[chunk.content for chunk in batch_chunks],
                    metadatas=[
                        {
                            "source_file": chunk.source_file,
                            "page_number": str(chunk.page_number) if chunk.page_number else "0",
                            "chunk_index": str(chunk.chunk_index),
                            **chunk.metadata
                        }
                        for chunk in batch_chunks
                    ]
                )

            logger.info(
                f"Added batch {i // batch_size + 1}"
            )
            # self.collection.add(
            #     ids=[chunk.id for chunk in chunks],
            #     embeddings=embeddings,
            #     documents=[chunk.content for chunk in chunks],
            #     metadatas=[
            #         {
            #             "source_file": chunk.source_file,
            #             "page_number": str(chunk.page_number) if chunk.page_number else "0",
            #             "chunk_index": str(chunk.chunk_index),
            #             **chunk.metadata
            #         }
            #         for chunk in chunks
            #     ]
            # )
            logger.info(f"Added {len(chunks)} chunks to vector store")
        except Exception as e:
            logger.error(f"Error adding chunks to vector store: {e}")
            raise
    
    async def query(
        self,
        query_embedding: List[float],
        question: str,
        top_k: int = 5,
        threshold: float = 0.15
    ) -> List[RetrievedChunk]:
        """Advanced hybrid retrieval."""

        if not self.collection:
            await self.initialize()

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=max(top_k * 8, 20)
            )

            retrieved_chunks = []

            if not results or not results["documents"]:
                return []

            query_words = set(question.lower().split())

            seen_contents = set()

            for doc, distance, metadata in zip(
                results["documents"][0],
                results["distances"][0],
                results["metadatas"][0]
            ):

                semantic_score = 1 - distance

                doc_lower = doc.lower()

                keyword_matches = sum(
                    1 for word in query_words
                    if word in doc_lower
                )

                keyword_score = min(keyword_matches * 0.05, 0.25)

                final_score = semantic_score + keyword_score

                content_key = doc[:300].strip()

                if content_key in seen_contents:
                    continue

                seen_contents.add(content_key)

                if final_score >= threshold:

                    chunk = RetrievedChunk(
                        content=doc,
                        source_file=metadata.get(
                            "source_file",
                            "unknown"
                        ),
                        page_number=int(
                            metadata.get("page_number", 0)
                        ) or None,
                        relevance_score=round(final_score, 4),
                        chunk_index=int(
                            metadata.get("chunk_index", 0)
                        )
                    )

                    retrieved_chunks.append(chunk)

            retrieved_chunks.sort(
                key=lambda x: x.relevance_score,
                reverse=True
            )

            retrieved_chunks = retrieved_chunks[:top_k]

            logger.info(
                f"Retrieved {len(retrieved_chunks)} chunks"
            )

            return retrieved_chunks

        except Exception as e:
            logger.error(f"Error querying vector store: {e}")
            raise


from sentence_transformers import SentenceTransformer

class EmbeddingService:
    """Generate and manage embeddings using OpenAI."""
    
    def __init__(self):
        self.settings = get_settings()
        # from openai import AsyncOpenAI
        # self.client = AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(
            # 'all-mpnet-base-v2'
            # 'all-MiniLM-L6-v2'
            'BAAI/bge-small-en-v1.5',
            device='cpu' # for BAAI
        )
        
    
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text."""
        try:
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            if not texts:
                return []
            
            # embeddings = self.model.encode(texts)
            embeddings = self.model.encode(
                texts,
                batch_size=128,
                show_progress_bar=True,
                convert_to_numpy=True,
                normalize_embeddings=True
            )

            logger.info(f"Generated {len(embeddings)} embeddings")
            
            return embeddings.tolist()
        
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise


class RAGSystem:
    """Complete RAG pipeline."""
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.embedding_service = EmbeddingService()
        self.settings = get_settings()
    
    async def initialize(self):
        """Initialize RAG system."""
        await self.vector_store.initialize()
        logger.info("RAG system initialized")
    
    async def ingest_document(self, chunks: List[DocumentChunk]) -> bool:
        """Ingest document chunks into RAG system."""
        try:
            if not chunks:
                logger.warning("No chunks to ingest")
                return False
            
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = await self.embedding_service.embed_batch(chunk_texts)
            
            await self.vector_store.add_chunks(chunks, embeddings)
            logger.info(f"Ingested {len(chunks)} chunks")
            return True
        except Exception as e:
            logger.error(f"Error ingesting document: {e}")
            raise
    
    async def retrieve_context(
        self,
        question: str,
        top_k: int = 5,
        threshold: float = 0.3
    ) -> Tuple[List[RetrievedChunk], List[float]]:
        """Retrieve relevant chunks for a question."""
        try:
            question_embedding = await self.embedding_service.embed_text(question)
            # retrieved_chunks = await self.vector_store.query(
            #     query_embedding=question_embedding,
            #     top_k=top_k,
            #     threshold=threshold
            # )

            retrieved_chunks = await self.vector_store.query(
                query_embedding=question_embedding,
                question=question,
                top_k=top_k,
                threshold=threshold
            )

            unique_contents = set()
            unique_chunks = []

            for chunk in retrieved_chunks:
                content_key = chunk.content[:200]

                if content_key not in unique_contents:
                    unique_contents.add(content_key)
                    unique_chunks.append(chunk)

            retrieved_chunks = unique_chunks


            logger.info(f"Retrieved {len(retrieved_chunks)} relevant chunks for question")
            return retrieved_chunks, question_embedding
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            raise
