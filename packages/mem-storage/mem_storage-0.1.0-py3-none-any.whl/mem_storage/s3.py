"""S3-compatible storage client for Hetzner Object Storage / MinIO."""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, BinaryIO

import aioboto3
from botocore.config import Config

from mem_common.config import get_settings


class S3Client:
    """Async S3-compatible storage client."""

    def __init__(
        self,
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        region: str | None = None,
    ):
        settings = get_settings()
        self._endpoint_url = endpoint_url or settings.s3_endpoint_url
        self._access_key_id = access_key_id or settings.s3_access_key_id
        self._secret_access_key = secret_access_key or settings.s3_secret_access_key
        self._region = region or settings.s3_region
        self._session = aioboto3.Session()

    @asynccontextmanager
    async def _get_client(self) -> AsyncGenerator[Any, None]:
        """Get an S3 client from the session."""
        async with self._session.client(
            "s3",
            endpoint_url=self._endpoint_url,
            aws_access_key_id=self._access_key_id,
            aws_secret_access_key=self._secret_access_key,
            region_name=self._region,
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            ),
        ) as client:
            yield client

    async def upload_bytes(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload bytes to S3 and return the object URL."""
        async with self._get_client() as client:
            await client.put_object(
                Bucket=bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
        return f"s3://{bucket}/{key}"

    async def upload_file(
        self,
        bucket: str,
        key: str,
        file_path: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload a file to S3 and return the object URL."""
        async with self._get_client() as client:
            await client.upload_file(
                Filename=file_path,
                Bucket=bucket,
                Key=key,
                ExtraArgs={"ContentType": content_type},
            )
        return f"s3://{bucket}/{key}"

    async def upload_fileobj(
        self,
        bucket: str,
        key: str,
        fileobj: BinaryIO,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload a file object to S3 and return the object URL."""
        async with self._get_client() as client:
            await client.upload_fileobj(
                Fileobj=fileobj,
                Bucket=bucket,
                Key=key,
                ExtraArgs={"ContentType": content_type},
            )
        return f"s3://{bucket}/{key}"

    async def download_bytes(self, bucket: str, key: str) -> bytes:
        """Download an object as bytes."""
        async with self._get_client() as client:
            response = await client.get_object(Bucket=bucket, Key=key)
            async with response["Body"] as stream:
                return await stream.read()

    async def download_file(self, bucket: str, key: str, file_path: str) -> str:
        """Download an object to a file and return the file path."""
        async with self._get_client() as client:
            await client.download_file(
                Bucket=bucket,
                Key=key,
                Filename=file_path,
            )
        return file_path

    async def get_presigned_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
        method: str = "get_object",
    ) -> str:
        """Generate a presigned URL for temporary access."""
        async with self._get_client() as client:
            return await client.generate_presigned_url(
                ClientMethod=method,
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires_in,
            )

    async def delete_object(self, bucket: str, key: str) -> None:
        """Delete an object from S3."""
        async with self._get_client() as client:
            await client.delete_object(Bucket=bucket, Key=key)

    async def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> list[dict[str, Any]]:
        """List objects in a bucket with optional prefix."""
        async with self._get_client() as client:
            response = await client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix,
                MaxKeys=max_keys,
            )
            return response.get("Contents", [])

    async def object_exists(self, bucket: str, key: str) -> bool:
        """Check if an object exists."""
        async with self._get_client() as client:
            try:
                await client.head_object(Bucket=bucket, Key=key)
                return True
            except client.exceptions.ClientError:
                return False

    async def get_object_metadata(
        self,
        bucket: str,
        key: str,
    ) -> dict[str, Any] | None:
        """Get object metadata (size, content-type, etc.)."""
        async with self._get_client() as client:
            try:
                response = await client.head_object(Bucket=bucket, Key=key)
                return {
                    "size": response.get("ContentLength"),
                    "content_type": response.get("ContentType"),
                    "last_modified": response.get("LastModified"),
                    "etag": response.get("ETag"),
                }
            except client.exceptions.ClientError:
                return None

    async def create_bucket(self, bucket: str) -> None:
        """Create a bucket if it doesn't exist."""
        async with self._get_client() as client:
            try:
                await client.create_bucket(Bucket=bucket)
            except client.exceptions.BucketAlreadyOwnedByYou:
                pass
            except client.exceptions.BucketAlreadyExists:
                pass

    @staticmethod
    def parse_s3_url(url: str) -> tuple[str, str]:
        """Parse an s3:// URL into bucket and key."""
        if not url.startswith("s3://"):
            raise ValueError(f"Invalid S3 URL: {url}")
        path = url[5:]  # Remove 's3://'
        parts = path.split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid S3 URL: {url}")
        return parts[0], parts[1]
