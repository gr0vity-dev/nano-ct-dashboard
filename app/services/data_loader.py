from typing import Protocol, Union, List, Dict, Any, Optional
from asyncio import gather

class IDataLoaderProtocol(Protocol):

    def set_url(self, url: str) -> None:
        pass

    async def load(self) -> Any:
        pass

class IDataFetcher(Protocol):

    async def fetch_data(self, url: str, from_cache: bool) -> Any:
        pass

class ILoaderFactory(Protocol):

    def set_urls(self, url: str) -> None:
        pass

    def get_primary_urls(self) -> List['UrlContext']:
        pass

    def get_additional_urls(self, data: Any) -> Union[None, List['UrlContext']]:
        pass

    def format_data(self, data: Any) -> Any:
        pass

class UrlContext:
    def __init__(self, url: str, context: Any = None):
        self.url = url
        self.context = context

class UrlBuilder:

    PR_MAPPING_BASE_URL = "https://api.github.com/search/issues?q=sha:{}+is:pull-request"
    REPOSITORY_URL = "https://api.github.com/repos/nanocurrency/nano-node"
    BUILDS_URL = 'https://raw.githubusercontent.com/gr0vity-dev/nano-node-builder/main/docker_builder/builds.json'
    TESTRUNS_LIST_URL = 'https://api.github.com/repos/gr0vity-dev/nano-node-builder/contents/continuous_testing'

    @staticmethod
    def get_testruns(testruns: List[Dict[str, Any]]) -> List[UrlContext]:
        urls = []
        for run in testruns:
            if isinstance(run, dict) and run.get("type") in ["commit", "pull_request"]:
                url = UrlBuilder._construct_url(run["hash"], run.get("pull_request"), run["type"])
                if url:
                    context_info = {
                        "original_data": run,
                        "repository_url": UrlBuilder.REPOSITORY_URL  # Include the repository_url in the context
                    }
                    urls.append(UrlContext(url, context_info))
        return urls


    @staticmethod
    def get_builds() -> List[UrlContext]:
        # Given the URL, the context can be the URL itself or any other relevant data
        return UrlContext(UrlBuilder.BUILDS_URL, {"context_type": "build", "url": UrlBuilder.BUILDS_URL})

    @staticmethod
    def get_reports() -> List[UrlContext]:
        # Given the URL, the context can be the URL itself or any other relevant data
        return UrlContext(UrlBuilder.TESTRUNS_LIST_URL, {"context_type": "report", "url": UrlBuilder.TESTRUNS_LIST_URL})

    @staticmethod
    def _construct_url(hash_value: str, pr_number: Union[None, int], entry_type: str) -> Union[None, str]:
        if entry_type == "commit":
            return UrlBuilder.PR_MAPPING_BASE_URL.format(hash_value)
        elif entry_type == "pull_request" and pr_number:
            return f"{UrlBuilder.REPOSITORY_URL}/pulls/{pr_number}"



class DataLoader:
    def __init__(self, data_fetcher: IDataFetcher):
        self.data_fetcher = data_fetcher

    async def load(self, factory: ILoaderFactory, url_context: UrlContext) -> Any:
        factory.set_urls(url_context)
        data = await self._fetch_data(factory.get_primary_urls())

        additional_urls = factory.get_additional_urls(data)
        if additional_urls:
            data = await self._fetch_data(additional_urls)

        return factory.format_data(data)

    async def load_many(self, factory: ILoaderFactory, url_contexts: List[UrlContext]) -> Any:
        factory.set_urls(url_contexts)
        data = await self._fetch_data(factory.get_primary_urls())

        additional_urls = factory.get_additional_urls(data)
        if additional_urls:
            data += await self._fetch_data(additional_urls)  # assuming you want to append the results

        return factory.format_data(data)

    async def _fetch_data(self, url_contexts: List[UrlContext]) -> List[Any]:
        return await gather(*(self.data_fetcher.fetch_data(uc.url) for uc in url_contexts))

class FileLoaderFactory:

    def set_urls(self, url_context: UrlContext) -> None:
        self.url = url_context.url

    def get_primary_urls(self) -> List[UrlContext]:
        return [UrlContext(self.url)]

    def get_additional_urls(self, data: Any) -> None:
        return None

    def format_data(self, data: Any) -> Any:
        return data[0]

class TestReportsLoaderFactory:

    def set_urls(self, url_context: UrlContext) -> None:
        self.url = url_context.url

    def get_primary_urls(self) -> List[UrlContext]:
        return [UrlContext(self.url)]

    def get_additional_urls(self, testruns_list: List[Dict[str, Any]]) -> List[UrlContext]:
        result = [UrlContext(testrun_file["download_url"]) for testrun_file in testruns_list[0] if testrun_file.get("name", "").endswith(".json")]
        return result

    def format_data(self, data: Any) -> Any:
        return data




class MappingsLoaderFactory:

    def __init__(self, urls: List[UrlContext] = None):
        self.urls = urls or []

    def set_urls(self, urls: List[UrlContext]) -> None:
        self.urls = urls

    def format_data(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        post_processed_data = {}
        for uc, data in zip(self.get_primary_urls(), results):
            key = uc.context.get("original_data", {}).get("hash", "")

            if "items" in data: # data coming from a commit
                repository_url_from_context = uc.context.get("repository_url")
                matching_items = [item for item in data.get("items", []) if item.get("repository_url") == repository_url_from_context]
                post_processed_data[key] = matching_items[0] if matching_items else None
            else:  #data coming from a pull request
                post_processed_data[key] = data
        return post_processed_data

    def get_primary_urls(self) -> List[UrlContext]:
        return self.urls or []

    def get_additional_urls(self, data: Any) -> Optional[List[UrlContext]]:
        return None

