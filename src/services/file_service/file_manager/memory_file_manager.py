import os

from .file_manager_base import FileManagerBase


class MemoryFileManager(FileManagerBase):
    storage = {}

    def __init__(self, config, ttl):
        self.config = config
        self.ttl = ttl

    def upload_from_buffer(self, buffer: bytes, file_name: str, **kwargs) -> dict:
        file_signature = self._generate_file_signature(file_name)
        metadata = self._create_metadata(
            file_signature, file_name, buffer, kwargs
        )
        metadata_name = self._get_metadata_name(file_signature)
        self.storage[file_signature] = buffer
        self.storage[metadata_name] = metadata
        return metadata

    def upload_from_file(self, file_path: str, **kwargs) -> dict:
        """
        Upload a file from a file path.
        kwargs are added to metadata
        """
        with open(file_path, "rb") as file:
            buffer = file.read()
        return self.upload_from_buffer(buffer, os.path.basename(file_path), **kwargs)

    def download_to_buffer(self, file_name: str) -> bytes:
        if not file_name in self.storage:
            raise FileNotFoundError(f"The file {file_name} does not exist.")
        return self.storage[file_name]

    def download_to_file(self, file_name: str, destination_path: str):
        with open(destination_path, "wb") as file:
            file.write(self.download_to_buffer(file_name))

    def delete_by_name(self, file_name: str):
        metadata_name = self._get_metadata_name(file_name)
        if file_name in self.storage:
            del self.storage[file_name]
        if metadata_name in self.storage:
            del self.storage[metadata_name]

    def get_metadata(self, file_name: str) -> dict:
        metadata_name = self._get_metadata_name(file_name)
        if metadata_name in self.storage:
            return self.storage[metadata_name]
        raise FileNotFoundError(f"The file {file_name} does not exist.")
    
    def update_file_expiration(self, file_signature, expiration_timestamp):
        metadata_name = self._get_metadata_name(file_signature)
        if metadata_name in self.storage:
            metadata = self.storage[metadata_name]
            metadata["expiration_timestamp"] = expiration_timestamp
            self.storage[metadata_name] = metadata
        else:
            raise FileNotFoundError(f"The file {file_signature} does not exist.")

    def list_all_metadata(self) -> list:
        return [data for key, data in self.storage.items() if key.endswith(".metadata")]
