"""
filetrans local filesystem storage backend
"""

import os
import shutil
from pathlib import Path
from typing import Tuple
from .base import StorageBackend


class LocalStorage(StorageBackend):
    """本地文件系统存储"""

    def __init__(self, config: dict):
        super().__init__(config)
        self.root_dir = Path(config['storage']['local']['root_dir'])
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = config['storage']['base_url']

    async def generate_upload_url(
        self,
        user_id: str,
        code: str,
        filename: str,
        ttl_seconds: int
    ) -> Tuple[str, str]:
        """生成上传 URL（本地模式返回完整路径）"""
        storage_key = self.generate_storage_key(user_id, code, filename)
        file_path = self.root_dir / storage_key
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 本地模式：upload_url 实际上是服务器接收上传的端点
        upload_url = f"{self.base_url}/api/upload/{storage_key}"
        return upload_url, storage_key

    async def generate_download_url(
        self,
        storage_key: str,
        ttl_seconds: int
    ) -> str:
        """生成下载 URL"""
        return f"{self.base_url}/api/download/{storage_key}"

    async def delete_file(self, storage_key: str) -> bool:
        """删除文件"""
        file_path = self.root_dir / storage_key
        try:
            if file_path.exists():
                if file_path.is_file():
                    file_path.unlink()
                else:
                    shutil.rmtree(file_path)

                # 清理空目录
                parent = file_path.parent
                while parent != self.root_dir and parent.exists():
                    if not any(parent.iterdir()):
                        parent.rmdir()
                        parent = parent.parent
                    else:
                        break
                return True
        except Exception as e:
            pass  # Silently fail
        return False

    async def file_exists(self, storage_key: str) -> bool:
        """检查文件是否存在"""
        file_path = self.root_dir / storage_key
        return file_path.exists()

    def get_full_path(self, storage_key: str) -> Path:
        """获取文件的完整路径"""
        return self.root_dir / storage_key
