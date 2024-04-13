from abc import ABC, abstractmethod


class StorageInterface(ABC):

    @abstractmethod
    def put(self, key, data):
        pass

    @abstractmethod
    def get(self, key):
        pass

    @abstractmethod
    def get_all(self):
        pass
