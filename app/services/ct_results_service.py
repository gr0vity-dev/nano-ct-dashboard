from app.services.cache_service import CacheService
from app.services.http_service import HttpService
from app.services.data_fetcher import DataFetcher
from app.services.github_helper import GithubUrlBuilder
from app.services.helper_service import DateTimeHelper
from app.services.data_combiner import DataCombiner
from app.services.data_service import DataService


class CTResultsService:

    def __init__(self):
        self.cache_service = CacheService()
        self.http_service = HttpService()
        self.data_fetcher = DataFetcher(self.cache_service, self.http_service)
        self.url_builder = GithubUrlBuilder()
        self.datetime_helper = DateTimeHelper()

    async def get_ct_results(self):
        # Pass instances to the data combiner
        await self.cache_service.connect()
        data_combiner = DataCombiner(self.url_builder, self.datetime_helper)

        # Use the DataService to combine all parts of the application
        data_service = DataService(data_combiner, self.data_fetcher)
        # Finally, you can call the fetch_and_combine_data method
        combined_data = await data_service.fetch_and_combine_data()
        return combined_data
