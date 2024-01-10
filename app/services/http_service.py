import aiohttp
import logging

# Initialize a logger
logger = logging.getLogger(__name__)


class HttpService:

    async def get(self, url, headers=None):
        headers = headers or {}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    response.raise_for_status()  # This will raise an error for 4xx and 5xx responses
                    response_status = response.status  # Return the response object
                    data = await response.text()
                    return response_status, data
            except aiohttp.ClientResponseError as error:
                logger.error(
                    "HTTP error encountered for URL: %s. Error: %s", url, error)
                if 'rate limit' in str(error):
                    return response.status, None
                else:
                    raise
            except Exception as error:
                logger.error(
                    "Exception encountered for URL: %s. Error: %s", url, error)
                raise
