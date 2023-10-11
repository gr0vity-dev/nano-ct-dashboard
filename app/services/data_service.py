from app.services.cache_service import CacheService
from app.services.data_fetcher import DataFetcher
from app.services.data_combiner import DataCombiner

from asyncio import gather
from app.services.data_fetcher import DataFetcher
from app.services.data_combiner import DataCombiner
# from app.services.report_combiner import DataCombiner
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
        pr_mapping_data = await self._fetch_all_pr_mappings(node_builds_test_report)

        print(pr_mapping_data)
        # enriched_reports = await self._enrich_reports_with_pr(node_builds_test_report)
        combined_data = self.data_combiner.combine_data(node_builds_status, node_builds_test_report, pr_mapping_data)

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

    # async def _enrich_reports_with_pr(self, all_testruns):
    #     pr_fetch_tasks = [self._fetch_pr_data(single_run) for single_run in all_testruns]
    #     return await gather(*pr_fetch_tasks)

    # async def _fetch_pr_data(self, single_run):
    #     if not single_run :
    #         return single_run
    #     if single_run.get("type") != "commit":
    #         return single_run

    #     single_run["pull_request"] = await self._fetch_pr_from_commit(single_run)
    #     return single_run

    # async def _fetch_pr_from_commit(self, testrun_data):
    #     mapping_url = self._construct_pr_mapping_url(testrun_data["hash"])
    #     mapping_data = await self.data_fetcher.fetch_data('map_issue', mapping_url)
    #     pr_number = self._extract_pr_number(mapping_data)

    #     return pr_number

    # def _extract_pr_number(self, mapping_data):
    #     for item in mapping_data.get("items", []):
    #         if item.get("repository_url") == self.REPOSITORY_URL:
    #             return str(item.get("number"))
    #     return None

    async def _fetch_all_pr_mappings(self, all_testruns):
        # Generate mapping tasks for both commits and pull requests
        mapping_tasks = [
            self._fetch_pr_mapping(run["hash"], run.get("pr_number"), run["type"])
            for run in all_testruns if run.get("type") in ["commit", "pull_request"]
        ]

        pr_mappings = await gather(*mapping_tasks)
        return {key: value for mapping in pr_mappings for key, value in mapping.items()}

    async def _fetch_pr_mapping(self, hash_value, pr_number, entry_type):
        # Depending on the type, construct the appropriate URL
        if entry_type == "commit":
            mapping_url = self._construct_commit_mapping_url(hash_value)
        elif entry_type == "pull_request" and pr_number:
            mapping_url = self._construct_pull_request_mapping_url(pr_number)
        else:
            return {hash_value: {}}

        mapping_data = await self.data_fetcher.fetch_data('map_issue', mapping_url)
        item = self._get_matching_item(mapping_data)
        return {hash_value: item}  # Always use hash_value as the key

    def _construct_commit_mapping_url(self, hash_value):
        return self.PR_MAPPING_BASE_URL.format(hash_value)

    def _construct_pull_request_mapping_url(self, pr_number):
        return f"{self.REPOSITORY_URL}/pulls/{pr_number}"



    def _get_matching_item(self, mapping_data):
        matching_items = [item for item in mapping_data.get("items", []) if item.get("repository_url") == self.REPOSITORY_URL]
        # Return the first matching item or None if no matches found
        return matching_items[0] if matching_items else None




