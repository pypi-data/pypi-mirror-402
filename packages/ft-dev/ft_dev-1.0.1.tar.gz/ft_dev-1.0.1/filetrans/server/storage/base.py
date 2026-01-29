"""
filetrans storage backend base class
"""

from abc import ABC, abstractmethod
from typing import Tuple
import uuid


class StorageBackend(ABC):
    """存储后端抽象基类"""

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    async def generate_upload_url(
        self,
        user_id: str,
        code: str,
        filename: str,
        ttl_seconds: int
    ) -> Tuple[str, str]:  # (upload_url, storage_key)
        """生成预签名上传 URL"""
        pass

    @abstractmethod
    async def generate_download_url(
        self,
        storage_key: str,
        ttl_seconds: int
    ) -> str:
        """生成预签名下载 URL"""
        pass

    @abstractmethod
    async def delete_file(self, storage_key: str) -> bool:
        """物理删除文件"""
        pass

    @abstractmethod
    async def file_exists(self, storage_key: str) -> bool:
        """检查文件是否存在"""
        pass

    def generate_storage_key(self, user_id: str, code: str, filename: str) -> str:
        """生成标准化的存储 Key"""
        uuid_suffix = uuid.uuid4().hex[:8]
        return f"{user_id}/{code}_{uuid_suffix}/{filename}"


def get_storage_backend(config: dict) -> StorageBackend:
    """获取存储后端实例"""
    backend_type = config['storage']['backend'].upper()

    if backend_type == 'LOCAL':
        from .local import LocalStorage
        return LocalStorage(config)
    elif backend_type == 'S3':
        from .s3 import S3Storage
        return S3Storage(config)
    else:
        raise ValueError(f"Unknown storage backend: {backend_type}")
