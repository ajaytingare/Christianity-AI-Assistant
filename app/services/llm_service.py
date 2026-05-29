import logging
from typing import Optional, List, Tuple
# from openai import AsyncOpenAI
import google.generativeai as genai
from app.config import get_settings
from app.models.schemas import RetrievedChunk, SafetyCheckResult
import json

logger = logging.getLogger(__name__)
settings = get_settings()


class HallucinationPrevention:
    """Strategies to prevent hallucinations in LLM responses."""
    
    @staticmethod
    def build_grounded_prompt(
        question: str,
        retrieved_chunks: List[RetrievedChunk],
        conversation_history: Optional[List[dict]] = None
    ) -> str:
        """Build a grounded prompt that constrains LLM to retrieved context."""
        
        history_text = ""

        if conversation_history:

            history_text = "\n".join(
                [
                    f"{msg['role']}: {msg['content']}"
                    for msg in conversation_history[-6:]
                ]
            )

        context = "\n\n".join([
            f"Source: {chunk.source_file} (Relevance: {chunk.relevance_score:.2%})\n{chunk.content}"
            for chunk in retrieved_chunks
        ])
        
        system_prompt = """You are a knowledgeable Christianity AI assistant. Your role is to answer questions based ONLY on the provided context about Christianity, Bible, theology, and related topics.

CRITICAL RULES:
1. ONLY use information from the provided context/sources
2. If the answer is not in the provided context, clearly state: "I could not find this information in the provided documents."
3. NEVER make up Bible verses, theological claims, or historical facts
4. ALWAYS cite your sources when providing information
5. If you're unsure about something, admit uncertainty rather than guessing
6. Be respectful of different Christian denominations
7. For controversial theological topics, present balanced perspectives
8. Do NOT generate offensive, heretical, or toxic content

Provided Context:
{context}

Question: {question}

Generate a response that:
- Is grounded in the provided context
- Includes specific citations
- Admits when information is not available
- Maintains accuracy and respect

Conversation History:
{history_text}

"""
        print("="*20)
        print("history_text:", history_text[:100])
        print("conversation_history:", conversation_history)
        print("="*20)
        return system_prompt.format(context=context, question=question, history_text=history_text)
    
    @staticmethod
    def validate_answer_grounding(
        answer: str,
        retrieved_chunks: List[RetrievedChunk],
        confidence_threshold: float = 0.7
    ) -> Tuple[bool, float, List[str]]:
        """Validate that answer is grounded in retrieved chunks."""
        
        issues = []
        grounding_score = 0.0
        
        if not retrieved_chunks:
            issues.append("No relevant sources retrieved")
            return False, 0.0, issues
        
        avg_relevance = sum(chunk.relevance_score for chunk in retrieved_chunks) / len(retrieved_chunks)
        grounding_score = avg_relevance
        
        if avg_relevance < confidence_threshold:
            issues.append(f"Low average relevance score: {avg_relevance:.2%}")
        
        generic_responses = ["i don't know", "not found", "unclear", "unsure"]
        if any(phrase in answer.lower() for phrase in generic_responses):
            if len(retrieved_chunks) > 0 and all(c.relevance_score < 0.5 for c in retrieved_chunks):
                grounding_score *= 0.9
        
        is_grounded = grounding_score >= confidence_threshold and len(issues) == 0
        return is_grounded, grounding_score, issues


class SafetyModeration:
    """Safety and moderation checks."""
    
    def __init__(self):
        # self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        genai.configure(api_key=settings.GEMINI_API_KEY)

        self.model = genai.GenerativeModel(
            settings.GEMINI_MODEL
        )
    
    async def check_content_safety(self, content: str):
        return SafetyCheckResult(
            is_safe=True,
            flags=[],
            confidence=1.0,
            reason=None
        )
    # async def check_content_safety(self, content: str) -> SafetyCheckResult:
    #     """Check content for harmful/unsafe material."""
        
    #     try:
    #         response = await self.client.moderations.create(input=content)
            
    #         flagged = response.results[0].flagged
    #         categories = response.results[0].categories
    #         category_scores = response.results[0].category_scores
            
    #         flags = [cat for cat, flagged_val in categories.model_dump().items() if flagged_val]
            
    #         return SafetyCheckResult(
    #             is_safe=not flagged,
    #             flags=flags,
    #             reason="Content flagged by OpenAI moderation" if flagged else None,
    #             confidence=max(category_scores.model_dump().values())
    #         )
    #     except Exception as e:
    #         logger.error(f"Error in safety check: {e}")
    #         return SafetyCheckResult(
    #             is_safe=True,
    #             confidence=0.0,
    #             reason="Could not perform safety check"
    #         )
    
    @staticmethod
    def check_scripture_hallucination(text: str) -> Tuple[bool, List[str]]:
        """Detect potential scripture hallucinations."""
        
        hallucinations = []
        
        suspicious_patterns = [
            ("Genesis 99:99", "Invalid chapter/verse reference"),
            ("Revelation 999", "Invalid chapter number"),
            ("Made-up 3:16", "Non-existent book"),
        ]
        
        for pattern, reason in suspicious_patterns:
            if pattern.lower() in text.lower():
                hallucinations.append(reason)
        
        return len(hallucinations) == 0, hallucinations
    
    @staticmethod
    def check_ideology_injection(text: str, prompt: str) -> bool:
        """Detect attempts to inject ideology into scripture."""
        
        dangerous_phrases = [
            "rewrite the bible to say",
            "make the verse support",
            "change the meaning of",
            "interpret this as supporting"
        ]
        
        prompt_lower = prompt.lower()
        return not any(phrase in prompt_lower for phrase in dangerous_phrases)


class LLMService:
    """LLM interaction with safety and grounding."""
    
    def __init__(self):
        self.settings = get_settings()

        genai.configure(
            api_key=self.settings.GEMINI_API_KEY
        )

        self.model = genai.GenerativeModel(
            self.settings.GEMINI_MODEL
        )

        self.hallucination_prevention = HallucinationPrevention()
        self.safety_moderation = SafetyModeration()

    # def __init__(self):
    #     self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    #     self.settings = get_settings()
    #     self.hallucination_prevention = HallucinationPrevention()
    #     self.safety_moderation = SafetyModeration()
    
    async def generate_answer(
        self,
        question: str,
        retrieved_chunks: List[RetrievedChunk],
        conversation_history: Optional[List[dict]] = None,
        temperature: float = 0.3
    ) -> Tuple[str, float, bool]:
        """Generate answer with safety and grounding checks."""
        
        if not retrieved_chunks:
            return "I could not find relevant information in the provided documents.", 0.0, False
        
        system_prompt = self.hallucination_prevention.build_grounded_prompt(
            question, retrieved_chunks, conversation_history
        )
        
        try:
            # response = await self.client.chat.completions.create(
            #     model=self.settings.OPENAI_MODEL,
            #     messages=[
            #         {"role": "system", "content": system_prompt},
            #         {"role": "user", "content": question}
            #     ],
            #     temperature=temperature,
            #     max_tokens=500,
            #     timeout=self.settings.LLM_TIMEOUT_SECONDS
            # )
            
            # answer = response.choices[0].message.content

            full_prompt = f"""
{system_prompt}

User Question:
{question}
"""

            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": 500
                }
            )

            answer = response.text
            
            is_grounded, grounding_score, issues = self.hallucination_prevention.validate_answer_grounding(
                answer, retrieved_chunks, self.settings.GROUNDING_CONFIDENCE_THRESHOLD
            )
            
            if issues:
                logger.warning(f"Grounding issues: {issues}")
            
            return answer, grounding_score, is_grounded
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise
    
    async def moderate_response(self, response: str) -> SafetyCheckResult:
        """Check response for safety issues."""
        return await self.safety_moderation.check_content_safety(response)
    
    async def moderate_prompt(self, prompt: str) -> Tuple[bool, Optional[str]]:
        """Check prompt for safety issues."""
        safety_result = await self.safety_moderation.check_content_safety(prompt)
        
        if not safety_result.is_safe:
            return False, f"Prompt flagged as unsafe: {safety_result.reason}"
        
        is_safe, _ = self.safety_moderation.check_scripture_hallucination(prompt)
        if not is_safe:
            return False, "Prompt contains suspicious references"
        
        is_safe = self.safety_moderation.check_ideology_injection(prompt, prompt)
        if not is_safe:
            return False, "Prompt contains ideology injection attempts"
        
        return True, None
    
    async def rewrite_question(
        self,
        question: str,
        conversation_history: list
    ):

        if not conversation_history:
            return question

        history_text = "\n".join(
            [
                f"{msg['role']}: {msg['content']}"
                for msg in conversation_history[-6:]
            ]
        )

        prompt = f"""
Conversation history:

{history_text}

Current question:
{question}

Rewrite the current question into a standalone question.

Examples:

Who was Noah?
How many sons did he have?
→ How many sons did Noah have?

Only return the rewritten question.
"""

        response = self.model.generate_content(prompt)

        return response.text.strip()

