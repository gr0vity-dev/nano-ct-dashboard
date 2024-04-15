
import asyncio
from processors.ct_processor import DataProcessor
from adapters.leveldb_adapter import LevelDBStorage
from database.sql_processor import SqlProcessor
from adapters.github_client import GitHubClient
from debug_secrets import GITHUB_TOKEN


async def scan_and_process_data():
    print("Scanning for new data...")
    leveldb_storage = LevelDBStorage("data_storage/leveldb_storage")
    sql_processor = SqlProcessor("data_storage/sqlite_storage.db")
    gh_client = GitHubClient(pat=GITHUB_TOKEN)

    processor = DataProcessor(leveldb_storage, sql_processor, gh_client)
    try:
        await processor.process_and_store_data()
        print("Data updated successfully")
    except Exception as e:
        print(f"Error updating data: {str(e)}")


async def main():
    await scan_and_process_data()

if __name__ == "__main__":
    asyncio.run(main())
