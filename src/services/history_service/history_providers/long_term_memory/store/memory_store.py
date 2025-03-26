from .store import Store

class MemoryStore(Store):
    """
    A simple in-memory store for storing history.
    """
    history = {}

    def store(self, key: str, data: dict):
        self.history[key] = data
    
    def retrieve(self, key: str):
        history = self.history.get(key, {})
        return history
    
    def delete(self, key: str):
        if key in self.history:
            del self.history[key]

    def keys(self):
        return list(self.history.keys())


