import aioredis
from aioredis.client import Redis
import pickle


class CacheService:
    CACHE_TTL = 24 * 60 * 60  # Cache for a whole day

    def __init__(self):
        self.redis = None

    async def connect(self):
        self.redis = Redis.from_url('redis://redis')

    async def close(self):
        if self.redis:
            self.redis.close()

    async def get_cache(self, key):
        value = await self.redis.get(key)
        if value is not None:
            return pickle.loads(value)

    async def set_cache(self, key, value, ttl=CACHE_TTL):
        value = pickle.dumps(value)
        await self.redis.set(key, value, ex=ttl)
