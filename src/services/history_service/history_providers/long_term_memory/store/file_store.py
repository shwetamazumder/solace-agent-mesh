import json

from .store import Store


class FileStore(Store):
    """
    A simple in-memory store for storing history.
    """
    history = {}

    def store(self, key: str, data: dict):
        print("Storing data", key, data)
        with open("tmp/history.jsonl", "a") as f:
            f.write(json.dumps({
                **data,
                "source": "store",
            }) + "\n")
        self.history[key] = data
    
    def retrieve(self, key: str):
        history = self.history.get(key, {})
        print("Retrieving data", history)
        with open("tmp/history.jsonl", "a") as f:
            f.write(json.dumps({
                **history,
                "source": "store",
            }) + "\n")
        return history
    
    def delete(self, key: str):
        if key in self.history:
            del self.history[key]

    def keys(self):
        return list(self.history.keys())


