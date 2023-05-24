from app.services.cache_service import CacheService
from app.services.data_fetcher import DataFetcher
from app.services.data_combiner import DataCombiner


class DataService:

    def __init__(self, cache_service: CacheService,
                 data_combiner: DataCombiner, data_fetcher: DataFetcher):
        self.cache_service = cache_service
        self.data_combiner = data_combiner
        self.data_fetcher = data_fetcher

    async def fetch_and_combine_data(self):
        builds_url = 'https://raw.githubusercontent.com/gr0vity-dev/nano-node-builder/main/docker_builder/builds.json'
        testruns_list_url = 'https://api.github.com/repos/gr0vity-dev/nano-node-builder/contents/continuous_testing'

        builds_res = await self.data_fetcher.fetch_data('build',
                                                        builds_url,
                                                        cache_duration=5 * 60)
        testruns_list = await self.data_fetcher.fetch_data(
            'testrun_list', testruns_list_url)

        # if not builds_res or not testruns_list:
        #     return {"error": "Failed to fetch data"}

        testruns_res = []
        for testrun_file in testruns_list:
            if testrun_file["name"].endswith(".json"):
                testrun_data = await self.data_fetcher.fetch_data(
                    'testrun', testrun_file["download_url"])
                if testrun_data:
                    testruns_res.append(testrun_data)

        combined_data = await self.data_combiner.combine_data(
            builds_res, testruns_res)
        return combined_data
