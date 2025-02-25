import uuid
import mimetypes
import re
import time
from abc import ABC, abstractmethod

from ..file_service_constants import FS_PROTOCOL, META_FILE_EXTENSION
from ..file_utils import get_file_schema_and_shape


MAX_NAME_LENGTH = 255 - (
    len(META_FILE_EXTENSION) + len(FS_PROTOCOL) + 3 + 36 + 1
)  # 36 is the length of a UUID, 3 is ://


class FileManagerBase(ABC):
    ttl: int

    def _generate_file_signature(self, file_name: str) -> str:
        """
        Generate a file signature from the original file name.
        """
        file_signature = str(uuid.uuid4())
        # Remove any leading or trailing whitespace
        file_name = file_name.strip()
        # Replace invalid characters and space/ampersand with underscores
        cleaned_name = re.sub(r'[<>:"/\\|?*& ]', "_", file_name)
        # replace unicode and binary characters with underscores
        cleaned_name = re.sub(r"[^\x00-\x7F]+", "_", cleaned_name)
        cleaned_name = re.sub(r"\\u[0-9a-fA-F]{4}", "_", cleaned_name)
        # Replace multiple underscores with a single underscore
        cleaned_name = re.sub(r"_+", "_", cleaned_name)
        # Truncate the signature if it is too long
        if len(cleaned_name) > MAX_NAME_LENGTH:
            start_index = len(cleaned_name) - MAX_NAME_LENGTH
            # Keep the latter portion of the name
            cleaned_name = cleaned_name[start_index:]
        signature = f"{file_signature}_{cleaned_name}"
        return signature

    def _get_url_from_signature(self, file_signature: str) -> str:
        """
        Generate a file URL from a file signature.
        """
        return f"{FS_PROTOCOL}://{file_signature}"

    def _get_mime_type(self, file_name: str) -> str:
        """
        Get the MIME type of a file.
        """
        mime_type, _ = mimetypes.guess_type(file_name)
        return mime_type

    def _get_metadata_name(self, name: str) -> dict:
        """
        Get metadata from a file URL.
        """
        metadata_path = f"{name}{META_FILE_EXTENSION}"
        return metadata_path

    def _create_metadata(self, file_signature: str, file_name: str, file: bytes, metadata: dict):
        """
        Extend metadata with schema and shape if not present
        Add file_size if not present
        """

        mime_type = self._get_mime_type(file_name)
        file_url = self._get_url_from_signature(file_signature)

        if not isinstance(metadata, dict):
            metadata = {}
        meta_copy = metadata.copy()

        # Can not be provided by user
        meta_copy["url"] = file_url

        if "mime_type" not in meta_copy:
            meta_copy["mime_type"] = mime_type

        if "name" not in meta_copy:
            meta_copy["name"] = file_name

        if (
            "schema-yaml" not in meta_copy
            or "schema_yaml" not in meta_copy
            or "shape" not in meta_copy
        ):
            schema, shape = get_file_schema_and_shape(file, meta_copy)
            if "schema-yaml" not in meta_copy and schema:
                meta_copy["schema-yaml"] = schema

            if "shape" not in meta_copy and shape:
                meta_copy["shape"] = shape
    
        if "file_size" not in meta_copy:
            meta_copy["file_size"] = len(file)

        if "upload_timestamp" not in meta_copy:
            meta_copy["upload_timestamp"] = time.time()

        if "expiration_timestamp" not in meta_copy:
            meta_copy["expiration_timestamp"] = meta_copy["upload_timestamp"] + self.ttl

        return meta_copy
    
    @abstractmethod
    def update_file_expiration(self, file_signature: str, expiration_timestamp: float):
        """
        Update the expiration timestamp for a file.
        """
        pass

    @abstractmethod
    def upload_from_buffer(self, buffer: bytes, file_name: str, **kwargs) -> dict:
        """
        Upload a file from a buffer.
        kwargs are added to metadata
        """
        pass

    @abstractmethod
    def upload_from_file(self, file_path: str, **kwargs) -> dict:
        """
        Upload a file from a file path.
        kwargs are added to metadata
        """
        pass

    @abstractmethod
    def download_to_buffer(self, file_name: str) -> bytes:
        """
        Download a file to a buffer.
        """
        pass

    @abstractmethod
    def download_to_file(self, file_name: str, destination_path: str):
        """
        Download a file to a destination path.
        """
        pass

    @abstractmethod
    def delete_by_name(self, file_name: str):
        """
        Delete a file by name.
        """
        pass

    @abstractmethod
    def get_metadata(self, file_name: str) -> dict:
        """
        Get metadata for a file.
        """
        pass

    @abstractmethod
    def list_all_metadata(self) -> list:
        """
        List all file metadata in the storage.
        """
        pass
