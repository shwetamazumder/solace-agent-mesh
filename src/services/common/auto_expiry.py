from abc import ABC, abstractmethod
import time 
import threading

from solace_ai_connector.common.log import log

class AutoExpiry(ABC):
    _expiry_thread = None
    expiration_check_interval = None
    _stop_expiry_thread = None


    def _start_auto_expiry_thread(self, expiration_check_interval):
        """Starts a background thread to handle auto-expiry."""
        self.expiration_check_interval = expiration_check_interval
        self._stop_expiry_thread = threading.Event()
        self._expiry_thread = threading.Thread(
            target=self._auto_expiry_task, daemon=True
        )
        self._expiry_thread.start()

    def _auto_expiry_task(self):
        """Background task to check and delete expired items."""
        while not self._stop_expiry_thread.is_set():
            try:
                self._delete_expired_items()
            except Exception as e:
                log.error(f"Error during auto-expiry process: {e}")
            time.sleep(self.expiration_check_interval)

    @abstractmethod
    def _delete_expired_items(self):
        """Checks all item and deletes those that have exceeded max_time_to_live."""
        raise NotImplementedError
        
    def stop_auto_expiry(self):
        """Stops the auto-expiry background thread."""
        if self._stop_expiry_thread:
            self._stop_expiry_thread.set()
        if self._expiry_thread and self._expiry_thread.is_alive():
            self._expiry_thread.join()

    def __del__(self):
        """Ensure the expiry thread stops when the service is destroyed."""
        self.stop_auto_expiry()
