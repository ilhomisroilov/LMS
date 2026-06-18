"""Redis client for caching, sessions and rate limiting."""
import redis

from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
