from urllib.parse import quote

import boto3
from botocore.exceptions import BotoCoreError, ClientError


class StorageError(Exception):
    pass


class StorageConfigurationError(StorageError):
    pass


class StorageObjectNotFoundError(StorageError):
    pass


class FileStorage:
    def __init__(self, bucket_name: str | None) -> None:
        self.bucket_name = bucket_name
        self.s3 = boto3.client("s3") if bucket_name else None

    def original_text_key(self, owner_user_id: str, reading_id: str) -> str:
        return self._key(owner_user_id, reading_id, "original.txt")

    def corrected_text_key(self, owner_user_id: str, reading_id: str) -> str:
        return self._key(owner_user_id, reading_id, "corrected.md")

    def recording_key(self, owner_user_id: str, reading_id: str, extension: str = "mp3") -> str:
        return self._key(owner_user_id, reading_id, f"recording.{extension}")

    def put_text(self, key: str, content: str, content_type: str) -> None:
        self.put_bytes(key, content.encode(), content_type)

    def put_bytes(self, key: str, content: bytes, content_type: str) -> None:
        if not self.s3 or not self.bucket_name:
            raise StorageConfigurationError("Files bucket is not configured")
        try:
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                ContentType=content_type,
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageError from exc

    def get_text(self, key: str) -> str:
        if not self.s3 or not self.bucket_name:
            raise StorageConfigurationError("Files bucket is not configured")
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            return response["Body"].read().decode()
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in {"NoSuchKey", "404"}:
                raise StorageObjectNotFoundError from exc
            raise StorageError from exc
        except BotoCoreError as exc:
            raise StorageError from exc

    def download_url(self, key: str, filename: str) -> str:
        if not self.s3 or not self.bucket_name:
            raise StorageConfigurationError("Files bucket is not configured")
        try:
            return self.s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": key,
                    "ResponseContentDisposition": (
                        f'attachment; filename="{quote(filename, safe="")}"'
                    ),
                },
                ExpiresIn=300,
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageError from exc

    def _key(self, owner_user_id: str, reading_id: str, filename: str) -> str:
        return f"users/{owner_user_id}/readings/{reading_id}/{filename}"
