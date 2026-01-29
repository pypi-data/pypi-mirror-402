"""
filetrans S3 storage backend
"""

import asyncio
from typing import Tuple
import boto3
from botocore.exceptions import ClientError
from .base import StorageBackend


class S3Storage(StorageBackend):
    """AWS S3 兼容存储"""

    def __init__(self, config: dict):
        super().__init__(config)
        s3_config = config['storage']['s3']

        self.bucket = s3_config['bucket']
        self.region = s3_config.get('region', 'us-east-1')
        self.endpoint_url = s3_config.get('endpoint_url')

        # 创建 S3 客户端
        self.s3_client = boto3.client(
            's3',
            region_name=self.region,
            endpoint_url=self.endpoint_url,
        )

        self.base_url = config['storage']['base_url']

    async def generate_upload_url(
        self,
        user_id: str,
        code: str,
        filename: str,
        ttl_seconds: int
    ) -> Tuple[str, str]:
        """生成 S3 预签名上传 URL"""
        storage_key = self.generate_storage_key(user_id, code, filename)

        loop = asyncio.get_event_loop()
        try:
            upload_url = await loop.run_in_executor(
                None,
                lambda: self.s3_client.generate_presigned_url(
                    'put_object',
                    Params={
                        'Bucket': self.bucket,
                        'Key': storage_key,
                    },
                    ExpiresIn=ttl_seconds,
                )
            )
            return upload_url, storage_key
        except ClientError as e:
            raise Exception(f"Failed to generate upload URL: {e}")

    async def generate_download_url(
        self,
        storage_key: str,
        ttl_seconds: int
    ) -> str:
        """生成 S3 预签名下载 URL"""
        loop = asyncio.get_event_loop()
        try:
            download_url = await loop.run_in_executor(
                None,
                lambda: self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.bucket,
                        'Key': storage_key,
                    },
                    ExpiresIn=ttl_seconds,
                )
            )
            return download_url
        except ClientError as e:
            raise Exception(f"Failed to generate download URL: {e}")

    async def delete_file(self, storage_key: str) -> bool:
        """删除 S3 对象"""
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(
                None,
                lambda: self.s3_client.delete_object(
                    Bucket=self.bucket,
                    Key=storage_key
                )
            )
            return True
        except ClientError as e:
            pass  # Silently fail
        return False

    async def file_exists(self, storage_key: str) -> bool:
        """检查 S3 对象是否存在"""
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(
                None,
                lambda: self.s3_client.head_object(
                    Bucket=self.bucket,
                    Key=storage_key
                )
            )
            return True
        except ClientError:
            return False
