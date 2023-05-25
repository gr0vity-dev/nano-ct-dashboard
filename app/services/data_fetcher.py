from app.services.cache_service import CacheService
from app.services.http_service import HttpService
import httpx


class DataFetcher:

    def __init__(self, cache_service: CacheService, http_service: HttpService):
        self.cache_service = cache_service
        self.http_service = http_service

    async def fetch_data(self,
                         data_type: str,
                         url: str,
                         add_cache=True,
                         cache_duration=None):
        data = await self.cache_service.get_cache(url)
        if data is not None:
            return data

        try:
            response = await self.http_service.get(url)
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            if 'rate limit' in str(error):
                return None
            raise error

        if response.status_code == 200:
            data = response.json()
            if add_cache:
                ttl = cache_duration if cache_duration is not None else CacheService.CACHE_TTL
                await self.cache_service.set_cache(url, data, ttl)
            return data
        elif data_type == 'testrun' and response.status_code == 404:
            return None
