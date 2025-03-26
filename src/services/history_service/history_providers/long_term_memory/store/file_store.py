"""
FileStore is a simple store that stores data in files.
"""

import json
import os
from .store import Store


class FileStore(Store):
    """
    A simple file store for storing data.
    """
    def __init__(self, config=None):
        super().__init__(config)

        if not self.config.get("path"):
            raise ValueError("Missing required configuration for FileStore, Missing 'path' in 'store_config'.")
        
        self.path = self.config.get("path")

        if not self._exists(self.path):
            os.makedirs(self.path, exist_ok=True)

    def store(self, key: str, data: dict):
        file_path = os.path.join(self.path, f"{key}.json")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(data))

    
    def retrieve(self, key: str):
        file_path = os.path.join(self.path, f"{key}.json")
        if not self._exists(file_path):
            return {}
        
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def delete(self, key: str):
        file_path = os.path.join(self.path, f"{key}.json")
        if self._exists(file_path):
            os.remove(file_path)

    def keys(self):
        return [f[:-5] for f in os.listdir(self.path) if f.endswith('.json')]
    
    def _exists(self, path: str):
        return os.path.exists(path)


