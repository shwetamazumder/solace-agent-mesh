import os
import json

from .file_manager_base import FileManagerBase
from ..file_service_constants import FS_PROTOCOL

DEFAULT_DIRECTORY = f"/tmp/{FS_PROTOCOL}"


class VolumeFileManager(FileManagerBase):

    def __init__(self, config, ttl):
        self.config = config
        self.ttl = ttl
        self.shared_volume_directory = config.get("directory", DEFAULT_DIRECTORY)
        if not os.path.exists(self.shared_volume_directory):
            os.makedirs(self.shared_volume_directory)

    def _save_metadata(self, file_path: str, metadata: dict):
        metadata_path = self._get_metadata_name(file_path)
        with open(metadata_path, "w", encoding="utf-8") as metadata_file:
            json.dump(metadata, metadata_file, indent=4)

    def upload_from_buffer(self, buffer: bytes, file_name: str, **kwargs) -> dict:
        file_signature = self._generate_file_signature(file_name)
        file_path = os.path.join(self.shared_volume_directory, file_signature)

        metadata = self._create_metadata(file_signature, file_name, buffer, kwargs)

        with open(file_path, "wb") as file:
            file.write(buffer)

        self._save_metadata(file_path, metadata)

        return metadata

    def upload_from_file(self, file_path: str, **kwargs) -> dict:
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")

        file_name = os.path.basename(file_path)

        with open(file_path, "rb") as source_file:
            buffer = source_file.read()

        return self.upload_from_buffer(buffer, file_name, **kwargs)

    def download_to_buffer(self, file_name: str) -> bytes:
        file_path = os.path.join(self.shared_volume_directory, file_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"The file at {file_name} does not exist in the shared volume."
            )

        with open(file_path, "rb") as file:
            buffer = file.read()

        return buffer

    def download_to_file(self, file_name: str, destination_path: str):
        buffer = self.download_to_buffer(file_name)
        with open(destination_path, "wb") as destination_file:
            destination_file.write(buffer)

    def get_metadata(self, file_name: str) -> dict:
        metadata_name = self._get_metadata_name(file_name)
        metadata_path = os.path.join(self.shared_volume_directory, metadata_name)

        if not os.path.exists(metadata_path):
            raise FileNotFoundError(
                f"The metadata for the file at {file_name} does not exist."
            )

        with open(metadata_path, "r", encoding="utf-8") as metadata_file:
            metadata = json.load(metadata_file)

        return metadata

    def delete_by_name(self, file_name: str):
        file_path = os.path.join(self.shared_volume_directory, file_name)
        metadata_path = self._get_metadata_name(file_path)

        # Delete the main file
        if os.path.exists(file_path):
            os.remove(file_path)
            os.remove(metadata_path)
        else:
            raise FileNotFoundError(
                f"The file at {file_name} does not exist in the shared volume."
            )
        
    def update_file_expiration(self, file_signature, expiration_timestamp):
        metadata = self.get_metadata(file_signature)
        metadata["expiration_timestamp"] = expiration_timestamp
        file_path = os.path.join(self.shared_volume_directory, file_signature)
        self._save_metadata(file_path, metadata)

    def list_all_metadata(self) -> list:
        all_metadata = []
        for file_name in os.listdir(self.shared_volume_directory):
            if file_name.endswith(".metadata"):
                metadata_path = os.path.join(self.shared_volume_directory, file_name)
                with open(metadata_path, "r", encoding="utf-8") as metadata_file:
                    metadata = json.load(metadata_file)
                    all_metadata.append(metadata)
        return all_metadata
