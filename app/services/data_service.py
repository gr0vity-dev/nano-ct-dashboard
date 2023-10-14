from app.services.cache_service import CacheService
from app.services.data_fetcher import DataFetcher
# from app.services.data_combiner import DataCombiner

from asyncio import gather
from app.services.data_fetcher import DataFetcher
#from app.services.data_combiner import DataCombiner
from app.services.report_combiner import DataCombiner
from app.services.data_loader import DataLoader, FileLoaderFactory, MappingsLoaderFactory, TestReportsLoaderFactory, UrlBuilder
import json




class DataService:



    def __init__(self, data_combiner: DataCombiner, data_fetcher: DataFetcher):
        self.data_combiner = data_combiner
        self.data_fetcher = data_fetcher

    async def fetch_and_combine_node_test_results(self):

        loader =  DataLoader(self.data_fetcher)

        builds_url_context = UrlBuilder.get_builds()
        node_builds_status = await loader.load(FileLoaderFactory(), builds_url_context)

        reports_url_context = UrlBuilder.get_reports()
        node_builds_test_report = await loader.load(TestReportsLoaderFactory(), reports_url_context)

        mappings_url_contexts = UrlBuilder.get_testruns(node_builds_test_report)
        pr_info = await loader.load_many(MappingsLoaderFactory(), mappings_url_contexts)

        combined_data = self.data_combiner.combine_data(node_builds_status, node_builds_test_report, pr_info)

        return combined_data




