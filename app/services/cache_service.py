import asyncpg
import pickle
from quart import current_app
# from app.secrets import *


class CacheService:

    def __init__(self):
        self.pool = None

    async def connect(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(user=current_app.config["PG_USER"],
                                                  password=current_app.config["PG_PW"],
                                                  database=current_app.config["PG_DB"],
                                                  host='postgres')
            # self.pool = await asyncpg.create_pool(user=PG_USER,
            #                                       password=PG_PW,
            #                                       database=PG_DB,
            #                                       host='localhost')

    async def close(self):
        if self.pool:
            await self.pool.close()

    async def get_cache(self, key):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('SELECT value FROM cache WHERE key = $1', key)
            if row:
                return pickle.loads(row['value'])

    async def insert_cache(self, key, value):
        pickled_value = pickle.dumps(value)
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO cache(key, value) VALUES($1, $2)
                ON CONFLICT (key) DO UPDATE SET value = $2
            ''', key, pickled_value)
    
    async def delete_cache(self, cache_key):       
        async with self.pool.acquire() as conn:
            await conn.execute('''
		DELETE FROM cache WHERE key LIKE '%' || $1 || '%'
            ''', cache_key)
