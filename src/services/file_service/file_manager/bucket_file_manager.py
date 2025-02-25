import boto3
import os
import json
from io import BytesIO
from botocore.exceptions import NoCredentialsError, ClientError

from .file_manager_base import FileManagerBase


class BucketFileManager(FileManagerBase):
    def __init__(self, config, ttl):
        self.config = config
        self.ttl = ttl
        self.bucket_name = config.get("bucket_name")
        self.boto3_config = config.get("boto3_config", {})
        self.endpoint_url = config.get("endpoint_url", None)
        session = boto3.Session(**self.boto3_config)
        s3_resource = session.resource("s3", endpoint_url=self.endpoint_url)
        try:
            if not self.bucket_name:
                raise Exception("Bucket name not provided.")

            bucket = s3_resource.Bucket(self.bucket_name)

            # Check if the bucket exists by attempting to load it
            bucket.load()
            self.bucket = bucket

        except ClientError as e:
            # Handle the case where the bucket doesn't exist or access is denied
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                raise Exception((f"Bucket '{self.bucket_name}' does not exist."), e)
            elif error_code == "403":
                raise Exception(
                    (f"Access to bucket '{self.bucket_name}' is denied."), e
                )
            else:
                raise Exception(f"Unexpected error: {e}")

    def _save_metadata(self, file_signature: str, metadata: dict):
        metadata_key = self._get_metadata_name(file_signature)
        metadata_content = json.dumps(metadata, indent=4)

        try:
            self.bucket.put_object(
                Key=metadata_key,
                Body=metadata_content,
                ContentType="application/json",
            )
        except (NoCredentialsError, ClientError) as e:
            raise RuntimeError(f"Failed to save metadata to S3: {str(e)}")

    def upload_from_buffer(self, buffer: bytes, file_name: str, **kwargs) -> dict:
        file_signature = self._generate_file_signature(file_name)
        metadata = self._create_metadata(file_signature, file_name, buffer, kwargs)

        try:
            self.bucket.put_object(
                Key=file_signature,
                Body=buffer,
                ContentType=metadata.get("mime_type") or "application/octet-stream",
            )
        except (NoCredentialsError, ClientError) as e:
            raise RuntimeError(f"Failed to upload file to S3: {str(e)}")

        self._save_metadata(file_signature, metadata)

        return metadata

    def upload_from_file(self, file_path: str, **kwargs) -> dict:
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")

        file_name = os.path.basename(file_path)
        file_signature = self._generate_file_signature(file_name)
        content_type = kwargs.get("mime_type") or self._get_mime_type(file_name) or "application/octet-stream"

        try:
            with open(file_path, "rb") as file_data:
                self.bucket.put_object(
                    Key=file_signature,
                    Body=file_data,
                    ContentType=content_type,
                )
                metadata = self._create_metadata(file_signature, file_name, file_data.read(), kwargs)
        except (NoCredentialsError, ClientError) as e:
            raise RuntimeError(f"Failed to upload file to S3: {str(e)}")

        self._save_metadata(file_signature, metadata)

        return metadata

    def download_to_buffer(self, file_name: str) -> bytes:
        try:
            buffer = BytesIO()
            obj = self.bucket.Object(file_name)
            obj.download_fileobj(buffer)
            buffer.seek(0)
            return buffer.read()
        except (NoCredentialsError, ClientError) as e:
            raise RuntimeError(f"Failed to download file from S3: {str(e)}")

    def download_to_file(self, file_name: str, destination_path: str):
        buffer = self.download_to_buffer(file_name)

        try:
            with open(destination_path, "wb") as destination_file:
                destination_file.write(buffer)
        except IOError as e:
            raise RuntimeError(f"Failed to write file to destination: {str(e)}")

    def get_metadata(self, file_name: str) -> dict:
        metadata_key = self._get_metadata_name(file_name)
        meta_buffer = self.download_to_buffer(metadata_key)
        return json.loads(meta_buffer)

    def delete_by_name(self, file_name: str):
        metadata_key = self._get_metadata_name(file_name)

        try:
            # the main file
            file = self.bucket.Object(file_name)
            # the metadata file
            meta = self.bucket.Object(metadata_key)

            # Delete the files
            file.delete()
            meta.delete()
        except (NoCredentialsError, ClientError) as e:
            raise RuntimeError(f"Failed to delete file from S3: {str(e)}")
        
    def update_file_expiration(self, file_signature, expiration_timestamp):
        metadata = self.get_metadata(file_signature)
        metadata["expiration_timestamp"] = expiration_timestamp
        self._save_metadata(file_signature, metadata)

    def list_all_metadata(self) -> list:
        all_metadata = []
        try:
            for obj in self.bucket.objects.all():
                if obj.key.endswith(".metadata"):
                    meta_buffer = self.download_to_buffer(obj.key)
                    metadata = json.loads(meta_buffer)

                    all_metadata.append(metadata)
        except (NoCredentialsError, ClientError) as e:
            raise RuntimeError(f"Failed to list metadata from S3: {str(e)}")
        return all_metadata
