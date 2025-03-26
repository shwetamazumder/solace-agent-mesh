from abc import ABC, abstractmethod


class Store(ABC):
    """
    Store base class.
    """

    def __init__(self, config=None):
        self.config = config or {}

    @abstractmethod
    def store(self, key: str, data: dict):
        """
        Store data in the store.

        :param key: The key to store the data under.
        :param data: The data to store.
        """
        pass

    @abstractmethod
    def retrieve(self, key: str):
        """
        Retrieve data from the store.

        :param key: The key to retrieve the data from.
        :return: The data stored under the key.
        """
        pass
    

    @abstractmethod
    def delete(self, key: str):
        """
        Delete data from the store.

        :param key: The key to delete the data from.
        """
        pass

    @abstractmethod
    def keys(self):
        """
        Retrieve the keys in the store.

        :return: The keys in the store.
        """
        pass


