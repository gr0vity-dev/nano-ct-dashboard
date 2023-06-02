import httpx


class HttpService:

    async def get_with_etag(self, url, etag):
        headers = {}
        if etag:
            pass
            #headers['If-None-Match'] = etag

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            return response

    async def get(self, url, headers= None):
        headers = headers if headers else {}     
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            return response
