import redis.asyncio as redis
from app.config import settings

# Create a connection pool to Redis
# decode_responses=True means Redis will automatically convert byte strings back to normal Python strings
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
