import sys
from adapters.leveldb_adapter import LevelDBStorage

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_pop_hash.py <hash>")
        sys.exit(1)

    hash_to_pop = sys.argv[1]  # Get the hash from command line argument

    leveldb_storage = LevelDBStorage("data_storage/leveldb_storage")
    if leveldb_storage.get(hash_to_pop) is not None:
        print(
            f"Found data for hash {hash_to_pop}: {leveldb_storage.get(hash_to_pop)}")
        leveldb_storage.pop(hash_to_pop)
        print(f"Data for hash {hash_to_pop} has been removed.")
    else:
        print(f"No data found for hash {hash_to_pop}.")
