"""
In-memory rate limiter for API requests.
"""

import time
from typing import Dict
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_calls: int, period_seconds: int):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            period_seconds: Time period in seconds
        """
        self.max_calls = max_calls
        self.period_seconds = period_seconds
        self.calls: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed for identifier.
        
        Args:
            identifier: Client identifier (e.g., IP address)
        
        Returns:
            True if request is allowed, False if rate limited
        """
        now = time.time()
        cutoff_time = now - self.period_seconds
        
        # Remove old entries
        self.calls[identifier] = [
            call_time for call_time in self.calls[identifier]
            if call_time > cutoff_time
        ]
        
        # Check if limit exceeded
        if len(self.calls[identifier]) >= self.max_calls:
            logger.warning(f"⚠️ Rate limit exceeded for {identifier}")
            return False
        
        # Record new call
        self.calls[identifier].append(now)
        return True
    
    def get_remaining(self, identifier: str) -> int:
        """Get remaining allowed calls for identifier."""
        now = time.time()
        cutoff_time = now - self.period_seconds
        
        valid_calls = [
            call_time for call_time in self.calls[identifier]
            if call_time > cutoff_time
        ]
        
        return max(0, self.max_calls - len(valid_calls))
    
    def cleanup(self, older_than_seconds: int = 3600) -> None:
        """
        Clean up old entries to save memory.
        
        Args:
            older_than_seconds: Remove entries older than this
        """
        now = time.time()
        cutoff_time = now - older_than_seconds
        
        cleaned = 0
        for identifier in list(self.calls.keys()):
            self.calls[identifier] = [
                call_time for call_time in self.calls[identifier]
                if call_time > cutoff_time
            ]
            
            if not self.calls[identifier]:
                del self.calls[identifier]
                cleaned += 1
        
        if cleaned > 0:
            logger.debug(f"🧹 Cleaned up {cleaned} old rate limit entries")


# Global rate limiter instance
_rate_limiter: RateLimiter = None


def get_rate_limiter(max_calls: int, period_seconds: int) -> RateLimiter:
    """Get or create global rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(max_calls, period_seconds)
    return _rate_limiter
