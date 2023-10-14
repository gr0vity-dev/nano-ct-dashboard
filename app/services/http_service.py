import httpx
import logging

# Initialize a logger
logger = logging.getLogger(__name__)

class HttpService:

    async def get_with_etag(self, url, etag):
        headers = {}
        if etag:
            pass
            #headers['If-None-Match'] = etag

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            return response

    async def get(self, url, headers=None):
        headers = headers if headers else {}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()  # Check for HTTP errors
                return response
            except httpx.HTTPStatusError as error:
                logger.error("HTTP error encountered for URL: %s. Error: %s", url, error)
                if 'rate limit' in str(error):
                    return None
                else:
                    raise error
