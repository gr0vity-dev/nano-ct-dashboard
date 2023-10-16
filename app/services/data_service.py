from app.services.cache_service import CacheService
from app.services.data_fetcher import DataFetcher
# from app.services.data_combiner import DataCombiner

from asyncio import gather
from app.services.data_fetcher import DataFetcher
#from app.services.data_combiner import DataCombiner
from app.services.report_combiner import DataCombiner
from app.services.data_loader import DataLoader, FileLoaderFactory, MappingsLoaderFactory, TestReportsLoaderFactory, UrlBuilder
from app.services.data_processor import PRInfoProcessor, BuildProcessor, TestrunProcessor
from app.services.data_stats import AdditionalStatsProcessor




class DataService:
    def __init__(self, data_fetcher: DataFetcher):
        self.data_fetcher = data_fetcher
        self.combined_stats = AdditionalStatsProcessor()

    async def fetch_and_combine_node_test_results(self):
        loaded_files = await self.load_files()
        data_combiner = self.init_data_combiner(loaded_files)
        combined_data = data_combiner.combine_data()
        self.combined_stats.compute(combined_data)

        return list(combined_data)[:100]


    async def load_files(self):
        loader = DataLoader(self.data_fetcher)

        builds_url_context = UrlBuilder.get_builds()
        node_builds_status = await loader.load(FileLoaderFactory(), builds_url_context)

        reports_url_context = UrlBuilder.get_reports()
        node_builds_test_report = await loader.load(TestReportsLoaderFactory(), reports_url_context)

        mappings_url_contexts = UrlBuilder.get_testruns(node_builds_test_report)
        pr_info = await loader.load_many(MappingsLoaderFactory(), mappings_url_contexts)

        return (node_builds_status, node_builds_test_report, pr_info)

    def init_data_combiner(self, loaded_files) -> DataCombiner:
        build_processor = BuildProcessor(UrlBuilder.REPOSITORY_URL, loaded_files[0])
        reports_processor = TestrunProcessor(loaded_files[1])
        pr_processor = PRInfoProcessor(loaded_files[2])

        processors = [build_processor, reports_processor, pr_processor]
        return DataCombiner(processors)





