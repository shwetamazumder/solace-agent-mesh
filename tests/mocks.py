import threading


class FlowLockManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.locks = {}

    def get_lock(self, lock_name):
        with self._lock:
            if lock_name not in self.locks:
                self.locks[lock_name] = threading.Lock()

            return self.locks[lock_name]


class FlowKVStore:
    def __init__(self):
        self.store = {}

    def set(self, key, value):
        self.store[key] = value

    def get(self, key):
        return self.store.get(key, None)
