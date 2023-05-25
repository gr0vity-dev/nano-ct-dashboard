from app.services.cache_service import CacheService
from app.services.http_service import HttpService
import logging


class DataFetcher:

    def __init__(self, cache_service: CacheService, http_service: HttpService):
        self.cache_service = cache_service
        self.http_service = http_service
        self.logger = logging.getLogger(
            __name__)  # Create a logger for this class
        self.logger.setLevel(logging.INFO)  # Set the logging level

        # If there are no handlers, add a StreamHandler to print logs to stdout
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)

    async def fetch_data(self,
                         data_type: str,
                         url: str,
                         add_cache=True,
                         cache_duration=None):
        data = self.cache_service.get_cache(url)
        if data is not None:
            self.logger.info('Cache hit for URL: %s',
                             url)  # Log when data is fetched from the cache
            return data

        self.logger.info(
            'Cache miss for URL: %s. Fetching from HTTP service...',
            url)  # Log when data is not in the cache and needs to be fetched
        response = await self.http_service.get(url)
        if response.status_code == 200:
            data = response.json()
            if add_cache:
                ttl = cache_duration if cache_duration is not None else CacheService.CACHE_TTL
                self.cache_service.set_cache(url, data, ttl)
                self.logger.info('Caching data for URL: %s',
                                 url)  # Log when data is cached
            return data
        elif data_type == 'testrun' and response.status_code == 404:
            # If a testrun is not found, it's not necessarily an error.
            return None
        else:
            response.raise_for_status()
