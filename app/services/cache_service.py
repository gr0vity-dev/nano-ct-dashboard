import asyncpg
import pickle
from quart import current_app

class CacheService:
    CACHE_TTL = 24 * 60 * 60  # Cache for a whole day

    def __init__(self):
        self.pool = None

    async def connect(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(user=current_app.config["PG_USER"],
						  password=current_app.config["PG_PW"],
                                                  database=current_app.config["PG_DB"],
						  host='postgres')

    async def close(self):
        if self.pool:
            await self.pool.close()

    async def get_cache(self, key):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('SELECT value FROM cache WHERE key = $1', key)
            if row:
                return pickle.loads(row['value'])

    async def set_cache(self, key, value, ttl=None):
        pickled_value = pickle.dumps(value)
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO cache(key, value) VALUES($1, $2)
                ON CONFLICT (key) DO UPDATE SET value = $2
            ''', key, pickled_value)
