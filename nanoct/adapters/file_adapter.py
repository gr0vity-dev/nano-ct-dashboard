import json
from interfaces.storage_interface import StorageInterface


class FileStorage(StorageInterface):
    def __init__(self, filepath="data_store.json"):
        self.filepath = filepath

    def put(self, key, value):
        """Stores data by key."""
        file_data = self._load_data()
        file_data[key] = value
        with open(self.filepath, "w") as file:
            json.dump(file_data, file, indent=4)

    def get(self, key):
        """Retrieves data by key, returning None if not found."""
        file_data = self._load_data()
        return file_data.get(key)

    def get_all(self):
        return self._load_data()

    def get_all_values(self):
        return list(self._load_data().values())

    def _load_data(self):
        """Loads the entire data store."""
        try:
            with open(self.filepath, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            return {}
