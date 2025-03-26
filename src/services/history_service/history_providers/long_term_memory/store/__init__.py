
from .store import Store
from .memory_store import MemoryStore
from .file_store import FileStore


def get_store(store_config: dict) -> Store:
    store_type = store_config.get("type", "memory")
    
    if store_type == "memory":
        return MemoryStore()
    elif store_type == "file":
        return FileStore()
    else:
        raise ValueError("Invalid store type. Choose 'memory' or 'file'.")