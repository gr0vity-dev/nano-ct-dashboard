from app.services.cache_service import CacheService
from app.services.http_service import HttpService
from quart import current_app
# from app.secrets import GITHUB_TOKEN
# import httpx
import json


class UnknownDataError(Exception):
    pass


class DataFetcher:

    def __init__(self, cache_service: CacheService, http_service: HttpService):
        self.cache_service = cache_service
        self.http_service = http_service

    async def fetch_data(self, url: str, from_cache=True):
        data = None

        if self.cache_service and from_cache:
            data = await self.cache_service.get_cache(url)

        if not data:
            # fetch data
            headers = {
                'Authorization': f'token {current_app.config["GITHUB_TOKEN"]}'}
            # headers = {'Authorization': f'token {GITHUB_TOKEN}'}
            response_status, data = await self.http_service.get(url, headers=headers)
            if not data:
                return {}
            data = json.loads(data)
            # Handling based on status code
            data = await self._handle_response_status(response_status, data, url)

        return data

    async def _handle_response_status(self, response_status, data, url):
        if response_status == 200:
            await self.cache_service.insert_cache(url, data)
            return data
        elif response_status == 404:
            # Custom logic for 404 if required can go here
            return None
        else:
            raise UnknownDataError(f"Unknown error for URL: {url}")
