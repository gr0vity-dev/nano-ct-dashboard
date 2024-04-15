from adapters.github_client import GitHubClient
from models.ct_results import TestResult
from database.sql_processor import SqlProcessor
from adapters.leveldb_adapter import LevelDBStorage
from datetime import datetime, timedelta, timezone
from json_relational import JsonRelational
from utils.logger import logger


class DataProcessor:
    def __init__(self, storage: LevelDBStorage, sql_processor: SqlProcessor):
        self.storage = storage
        self.sql_processor = sql_processor
        self.github_client = GitHubClient()

    async def fetch_builds_json(self):
        builds_url = "https://api.github.com/repos/gr0vity-dev/nano-node-builder/contents/docker_builder/builds.json"
        return await self.github_client.fetch_content_and_decode(builds_url)

    async def fetch_testrun_json(self, hash):
        test_url = f"https://api.github.com/repos/gr0vity-dev/nano-node-builder/contents/continuous_testing/{hash}.json"
        return await self.github_client.fetch_content_and_decode(test_url)

    def process_test_result(self, build):
        test_result = TestResult()
        test_result.load_from_builds(build)
        return test_result

    def convert_to_sql(self):
        jr = JsonRelational(root_name="builds")
        hashes = self.storage.get_all_values()
        json_tables = jr.flatten_json(hashes)
        self.sql_processor.write_to_db(json_tables)
        logger.info(f"{len(json_tables)} tables converted to sql")

    async def process_and_store_data(self):
        new_inserts = 0

        builds_json = await self.fetch_builds_json()

        for build in builds_json:
            test_result = self.process_test_result(build)
            hash = test_result.hash  # Assuming 'hash' is a unique identifier for each build
            test_run_stored = self.storage.get(hash)

            # Skip processing if test run shouldn't be processed
            if test_run_stored and not self.should_process_again(test_run_stored):
                continue

            # Process only if test_result meets conditions
            if test_result.build_status == 'pass' and test_result.built_at > '2023-12-31T23:59:59Z':
                testrun_json = await self.fetch_testrun_json(hash)
                if testrun_json:
                    test_result.load_from_testruns(testrun_json)
                    new_inserts += 1
                    logger.info(f"New {hash} has been inserted")
                else:
                    logger.warn(f"No result found for {hash}")

            self.storage.put(hash, test_result.to_json())

        logger.info(
            f"Processing finished with {new_inserts} new hashes" if new_inserts > 0 else "Processing finished")

        if new_inserts == 0:
            logger.info("Skip converting to sql")
        else:
            self.convert_to_sql()

    def should_process_again(self, stored_data):
        """Determines if the stored test run should be processed again."""
        if stored_data.get("overall_status") == "running":
            # Convert the stored datetime string to an offset-aware datetime using timezone.utc
            started_at = datetime.strptime((stored_data.get(
                "build_started_at") or "1970-01-01T00:00:00Z"), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

            # Compare with the current UTC time, which is also made offset-aware
            time_diff = datetime.now(timezone.utc) - started_at
            if time_diff < timedelta(hours=24):
                return True
        return False
