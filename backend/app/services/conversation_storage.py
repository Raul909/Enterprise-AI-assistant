"""
Conversation storage service.
Handles persistence of conversation context using Redis with an in-memory fallback.
"""

import json
from typing import Dict, Any, Optional

import redis
from core.config import settings
from core.logging import get_logger
from schemas.chat import ConversationContext

logger = get_logger(__name__)


class ConversationStorage:
    """
    Handles persistence of conversation context using Redis with an in-memory fallback.
    """

    def __init__(self):
        self._redis = None
        self._in_memory: Dict[str, str] = {}
        self._redis_enabled = False

        if settings.redis_url:
            try:
                self._redis = redis.from_url(settings.redis_url, decode_responses=True)
                # Test connection
                self._redis.ping()
                self._redis_enabled = True
                logger.info("Connected to Redis for conversation storage")
            except Exception as e:
                logger.error(
                    "Failed to connect to Redis. Falling back to in-memory storage.",
                    error=str(e),
                    redis_url=settings.redis_url
                )
                self._redis = None
        else:
            logger.info("Redis URL not configured. Using in-memory conversation storage.")

    def get(self, conversation_id: str) -> Optional[ConversationContext]:
        """
        Retrieve conversation context by ID.

        Args:
            conversation_id: Unique identifier for the conversation

        Returns:
            ConversationContext if found, None otherwise
        """
        data_json = None

        if self._redis_enabled and self._redis:
            try:
                data_json = self._redis.get(f"conv:{conversation_id}")
            except Exception as e:
                logger.error("Error reading from Redis", error=str(e), conversation_id=conversation_id)
                # Fallback to in-memory for this request if Redis fails

        if not data_json:
            data_json = self._in_memory.get(conversation_id)

        if not data_json:
            return None

        try:
            data_dict = json.loads(data_json)
            return ConversationContext.model_validate(data_dict)
        except Exception as e:
            logger.error(
                "Error deserializing conversation context",
                error=str(e),
                conversation_id=conversation_id
            )
            return None

    def set(self, conversation_id: str, context: ConversationContext) -> None:
        """
        Store conversation context.

        Args:
            conversation_id: Unique identifier for the conversation
            context: The ConversationContext object to store
        """
        try:
            data_json = context.model_dump_json()

            # Always update in-memory as a secondary cache/fallback
            self._in_memory[conversation_id] = data_json

            if self._redis_enabled and self._redis:
                try:
                    self._redis.set(
                        f"conv:{conversation_id}",
                        data_json,
                        ex=settings.cache_ttl_seconds
                    )
                except Exception as e:
                    logger.error("Error writing to Redis", error=str(e), conversation_id=conversation_id)
        except Exception as e:
            logger.error(
                "Error serializing conversation context",
                error=str(e),
                conversation_id=conversation_id
            )


# Global instance
conversation_storage = ConversationStorage()
