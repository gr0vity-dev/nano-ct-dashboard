import leveldb
from storage.interface import StorageInterface
import json


class LevelDBStorage(StorageInterface):
    def __init__(self, db_path="leveldb_storage"):
        self.db = leveldb.LevelDB(db_path)

    def put(self, key, value):
        """Stores data by key.
        Assumes `value` is a Python dictionary that should be stored as JSON."""
        # Serialize the value to JSON and then encode it to bytes before storing
        serialized_value = json.dumps(value).encode('utf-8')
        self.db.Put(key.encode('utf-8'), serialized_value)

    def get(self, key):
        """Retrieves data by key, returning None if not found.
        Returns the data deserialized from JSON."""
        try:
            value = self.db.Get(key.encode('utf-8'))
            # Decode the bytes to string and then deserialize from JSON
            return json.loads(value.decode('utf-8'))
        except KeyError:
            return None

    def get_all(self):
        """Retrieves all stored data, deserializing from JSON."""
        return {k.decode('utf-8'): json.loads(v.decode('utf-8')) for k, v in self.db.RangeIter()}

    def get_all_values(self):
        return list(self.get_all().values())

    def pop(self, key):
        """Removes the specified key from the database and returns its value,
        deserialized from JSON. If the key is not found, returns None."""
        try:
            # First, retrieve the value to return it later
            value = self.get(key)
            if value is not None:
                # If the key exists, delete it from the database
                self.db.Delete(key.encode('utf-8'))
            return value
        except KeyError:
            return None
