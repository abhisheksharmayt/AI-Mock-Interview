from app.cache.redis_client import redis_client

async def set_cache(key, value, ttl=60):
    await redis_client.set(key, value, ex=ttl)

async def get_cache(key):
    return await redis_client.get(key)