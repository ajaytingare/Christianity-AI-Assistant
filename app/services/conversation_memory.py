import logging
from typing import Optional, List
from datetime import datetime, timedelta
from app.models.schemas import ConversationMessage, ConversationContext
from app.utils.helpers import IDGenerator
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ConversationMemory:
    """Manage conversation history and context."""
    
    def __init__(self):
        self.conversations: dict[str, ConversationContext] = {}
        self.settings = get_settings()
        print("="*20)
        print("ConversationMemory instance:", id(self))
        print("="*20)
    
    def create_conversation(self, document_ids: Optional[List[str]] = None) -> str:
        """Create a new conversation."""
        conversation_id = IDGenerator.generate_conversation_id()
        now = datetime.utcnow()
        
        self.conversations[conversation_id] = ConversationContext(
            conversation_id=conversation_id,
            messages=[],
            created_at=now,
            last_updated=now,
            document_ids=document_ids or []
        )
        
        logger.info(f"Created conversation {conversation_id}")
        
        print("="*20)
        print(
            "CREATED:",
            conversation_id
        )
        print("="*20)

        return conversation_id
    
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[dict] = None
    ) -> Optional[ConversationMessage]:
        """Add message to conversation."""

        print("\nADD_MESSAGE")
        print("SELF ID:", id(self))
        print("CONV ID:", conversation_id)
        print("AVAILABLE:", list(self.conversations.keys()))
        
        if conversation_id not in self.conversations:
            logger.warning(f"Conversation {conversation_id} not found")
            return None
        
        conversation = self.conversations[conversation_id]
        
        if len(conversation.messages) >= self.settings.MAX_CONVERSATION_LENGTH:
            logger.warning(f"Conversation {conversation_id} at max length, removing oldest")
            conversation.messages.pop(0)
        
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        conversation.messages.append(message)
        conversation.last_updated = datetime.utcnow()
        
        return message
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationContext]:
        """Get conversation by ID."""

        print("\nGET_CONVERSATION")
        print("SELF ID:", id(self))
        print("CONV ID:", conversation_id)
        print("AVAILABLE:", list(self.conversations.keys()))
        
        if conversation_id not in self.conversations:
            logger.warning(f"Conversation {conversation_id} not found")
            return None
        
        conversation = self.conversations[conversation_id]
        
        ttl_hours = self.settings.CONVERSATION_TTL_HOURS
        age_hours = (datetime.utcnow() - conversation.created_at).total_seconds() / 3600
        
        if age_hours > ttl_hours:
            logger.info(f"Conversation {conversation_id} expired, removing")
            del self.conversations[conversation_id]
            return None
        
        print("="*20)
        print(
            "LOOKING FOR:",
            conversation_id
        )

        print(
            "AVAILABLE:",
            list(self.conversations.keys())
        )
        print("="*20)

        return conversation
    
    def get_message_history(
        self,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[dict]:
        """Get message history for conversation as list of dicts."""
        conversation = self.get_conversation(conversation_id)
        
        if not conversation:
            return []
        
        messages = conversation.messages
        if limit:
            messages = messages[-limit:]
        
        return [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in messages
        ]
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """Clear a conversation."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(f"Cleared conversation {conversation_id}")
            return True
        return False
    
    def cleanup_expired_conversations(self) -> int:
        """Remove expired conversations."""
        ttl_hours = self.settings.CONVERSATION_TTL_HOURS
        now = datetime.utcnow()
        
        expired_ids = []
        for conv_id, conversation in self.conversations.items():
            age_hours = (now - conversation.created_at).total_seconds() / 3600
            if age_hours > ttl_hours:
                expired_ids.append(conv_id)
        
        for conv_id in expired_ids:
            del self.conversations[conv_id]
        
        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired conversations")
        
        return len(expired_ids)
