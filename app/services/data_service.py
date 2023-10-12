from app.services.cache_service import CacheService
from app.services.data_fetcher import DataFetcher
from app.services.data_combiner import DataCombiner

from asyncio import gather
from app.services.data_fetcher import DataFetcher
#from app.services.data_combiner import DataCombiner
from app.services.report_combiner import DataCombiner
import json


class DataService:

    PR_MAPPING_BASE_URL = "https://api.github.com/search/issues?q=sha:{}+is:pull-request"
    REPOSITORY_URL = "https://api.github.com/repos/nanocurrency/nano-node"
    BUILDS_URL = 'https://raw.githubusercontent.com/gr0vity-dev/nano-node-builder/main/docker_builder/builds.json'
    TESTRUNS_LIST_URL = 'https://api.github.com/repos/gr0vity-dev/nano-node-builder/contents/continuous_testing'

    def __init__(self, data_combiner: DataCombiner, data_fetcher: DataFetcher):
        self.data_combiner = data_combiner
        self.data_fetcher = data_fetcher

    async def fetch_and_combine_node_test_results(self):
        node_builds_status = await self._fetch_builds_status()
        node_builds_test_report = await self._fetch_builds_test_report()
        pr_info = await self._fetch_all_pr_mappings(node_builds_test_report)

        # enriched_reports = await self._enrich_reports_with_pr(node_builds_test_report)
        combined_data = self.data_combiner.combine_data(node_builds_status, node_builds_test_report, pr_info)

        return combined_data


    def _is_commit_test_data(self, test_data):
        return test_data and test_data.get("type") == "commit"

    async def _fetch_builds_status(self):
        return await self.data_fetcher.fetch_data('build', self.BUILDS_URL, add_cache=False)

    async def _fetch_builds_test_report(self):
        testruns_list = await self.data_fetcher.fetch_data('testrun_list', self.TESTRUNS_LIST_URL, add_cache=False)
        fetch_tasks = [
            self.data_fetcher.fetch_data('testrun', testrun_file["download_url"])
            for testrun_file in testruns_list if testrun_file["name"].endswith(".json")
        ]
        return await gather(*fetch_tasks)


    async def _fetch_all_pr_mappings(self, all_testruns):
        # Generate mapping tasks for both commits and pull requests
        mapping_tasks = [
            self._fetch_pr_mapping(run["hash"], run.get("pull_request"), run["type"])
            for run in all_testruns if run.get("type") in ["commit", "pull_request"]
        ]

        pr_mappings = await gather(*mapping_tasks)
        return {key: value for mapping in pr_mappings for key, value in mapping.items()}

    async def _fetch_pr_mapping(self, hash_value, pr_number, entry_type):
        # Depending on the type, construct the appropriate URL
        if entry_type == "commit":
            mapping_url = self._construct_commit_mapping_url(hash_value)
            mapping_data = await self.data_fetcher.fetch_data('map_issue', mapping_url)
            item = self._get_matching_item(mapping_data)
        elif entry_type == "pull_request" and pr_number:
            mapping_url = self._construct_pull_request_mapping_url(pr_number)
            item = await self.data_fetcher.fetch_data('map_issue', mapping_url)
        else:
            return {hash_value: {}}


        return {hash_value: item}  # Always use hash_value as the key

    def _construct_commit_mapping_url(self, hash_value):
        return self.PR_MAPPING_BASE_URL.format(hash_value)

    def _construct_pull_request_mapping_url(self, pr_number):
        return f"{self.REPOSITORY_URL}/pulls/{pr_number}"



    def _get_matching_item(self, mapping_data):
        matching_items = [item for item in mapping_data.get("items", []) if item.get("repository_url") == self.REPOSITORY_URL]
        # Return the first matching item or None if no matches found
        return matching_items[0] if matching_items else None




