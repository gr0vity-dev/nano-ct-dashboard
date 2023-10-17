from app.services.cache_service import CacheService
from app.services.http_service import HttpService
from quart import current_app
import httpx


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

        if not data :
            # fetch data
            headers = {'Authorization': f'token {current_app.config["GITHUB_TOKEN"]}'}
            response = await self.http_service.get(url, headers=headers)

            #Handling based on status code
            data = await self._handle_response_status(response, url)

        return data

    async def _handle_response_status(self, response, url):
        if response.status_code == 200:
            data = response.json()
            if "overall_status" in data and data["overall_status"] != "running":
                await self.cache_service.insert_cache(url, data)
            return data
        elif response.status_code == 404:
            # Custom logic for 404 if required can go here
            return None
        else:
            raise UnknownDataError(f"Unknown error for URL: {url}")
