from app.services.cache_service import CacheService
from app.services.data_fetcher import DataFetcher
from app.services.data_combiner import DataCombiner

from asyncio import gather
from app.services.data_fetcher import DataFetcher
from app.services.data_combiner import DataCombiner


class DataService:

    def __init__(self, data_combiner: DataCombiner, data_fetcher: DataFetcher):
        self.data_combiner = data_combiner
        self.data_fetcher = data_fetcher

    async def fetch_pr_from_commit(self, testrun_data):
        testrun_pr_mapping = "https://api.github.com/search/issues?q=sha:{}"
        repository_url = "https://api.github.com/repos/nanocurrency/nano-node"

        mapping_url = testrun_pr_mapping.format(testrun_data["hash"])
        mapping_data = await self.data_fetcher.fetch_data(
            'map_issue', mapping_url)

        items = mapping_data.get("items", [])
        for item in items:
            if item.get("repository_url") == repository_url:
                return str(item.get("number"))

        return None

    async def fetch_pr_data(self, test_data):
        if test_data is None or test_data.get("type") != "commit":
            return test_data

        test_data["pull_request"] = await self.fetch_pr_from_commit(test_data)
        return test_data

    async def fetch_and_combine_data(self):
        builds_url = 'https://raw.githubusercontent.com/gr0vity-dev/nano-node-builder/main/docker_builder/builds.json'
        testruns_list_url = 'https://api.github.com/repos/gr0vity-dev/nano-node-builder/contents/continuous_testing'

        builds_res = await self.data_fetcher.fetch_data('build',
                                                        builds_url,
                                                        cache_duration=5 * 60)
        testruns_list = await self.data_fetcher.fetch_data(
            'testrun_list', testruns_list_url)

        # Build a list of tasks to run concurrently
        fetch_tasks = [
            self.data_fetcher.fetch_data('testrun',
                                         testrun_file["download_url"])
            for testrun_file in testruns_list
            if testrun_file["name"].endswith(".json")
        ]

        # Run all tasks concurrently
        testruns_data = await gather(*fetch_tasks)

        # Prepare tasks to fetch pull requests
        pr_fetch_tasks = [
            self.fetch_pr_data(test_data) for test_data in testruns_data
        ]

        # Run all tasks concurrently
        testruns_res = await gather(*pr_fetch_tasks)

        combined_data = await self.data_combiner.combine_data(
            builds_res, testruns_res)
        return combined_data
