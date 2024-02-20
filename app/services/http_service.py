import httpx
import aiohttp
import logging

# Initialize a logger
logger = logging.getLogger(__name__)


class HttpService:

    async def get_with_etag(self, url, etag):
        headers = {}
        if etag:
            pass
            # headers['If-None-Match'] = etag

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            return response

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

    # async def get(self, url, headers=None):
    #     headers = headers if headers else {}
    #     async with httpx.AsyncClient() as client:
    #         try:
    #             response = await client.get(url, headers=headers)
    #             response.raise_for_status()  # Check for HTTP errors
    #             return response
    #         except httpx.HTTPStatusError as error:
    #             logger.error(
    #                 "HTTP error encountered for URL: %s. Error: %s", url, error)
    #             if 'rate limit' in str(error):
    #                 return None
    #             else:
    #                 raise error
    #         except Exception as error:
    #             logger.error(
    #                 "Exception encountered for URL: %s. Error: %s", url, error)
    #         return None
