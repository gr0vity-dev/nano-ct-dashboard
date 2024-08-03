import aiohttp
import base64
import json
import logging
from os import getenv


class GitHubClient:
    def __init__(self, pat=None):
        self.pat = pat or getenv("GITHUB_TOKEN")

    async def fetch_json(self, url):
        headers = {'Authorization': f'token {self.pat}'}
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url) as response:
                    if response.status == 404:
                        logging.warning(f"URL not found: {url}")
                        return None  # Return None to indicate not found or error
                    response.raise_for_status()  # Will raise for other HTTP errors
                    return await response.json()
        except aiohttp.ClientError as e:
            logging.error(f"Failed to fetch URL {url}: {e}")
            return None

    async def fetch_git_url(self, url):
        data = await self.fetch_json(url)
        if data is None:
            return None  # Early exit if fetch failed or not found
        try:
            return data['git_url']
        except Exception as e:
            logging.error(f"Failed to get git_url from JSON {url}: {e}")
            return None

    async def fetch_content_and_decode(self, url):
        data = await self.fetch_json(url)
        if data is None:
            return None  # Early exit if fetch failed or not found
        try:
            decoded_content = base64.b64decode(data['content']).decode('utf-8')
            return json.loads(decoded_content)
        except Exception as e:
            logging.error(f"Failed to decode or parse JSON from {url}: {e}")
            return None
