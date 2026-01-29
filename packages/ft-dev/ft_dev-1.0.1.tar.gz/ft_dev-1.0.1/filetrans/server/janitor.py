"""
filetrans janitor - automatic file cleanup service
"""

import asyncio
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import func

from .database import get_db_session
from .models import Transfer, SystemConfig, Token
from .storage.base import get_storage_backend


class FileJanitor:
    """文件清理服务"""

    def __init__(self, config: dict, storage_backend):
        self.config = config
        self.storage = storage_backend
        self.interval = config.get('janitor', {}).get('interval_seconds', 60)
        self.running = False

    async def start(self):
        """启动清理任务"""
        self.running = True
        while self.running:
            try:
                await self.cleanup_expired()
                await self.check_disk_space()
            except Exception as e:
                pass  # Silently continue on error

            await asyncio.sleep(self.interval)

    def stop(self):
        """停止清理任务"""
        self.running = False

    async def cleanup_expired(self):
        """清理过期文件"""
        db = get_db_session()

        now = datetime.now()

        # 查找过期或下载次数超限的文件
        expired = db.query(Transfer).filter(
            (
                (Transfer.expire_at < now) |
                ((Transfer.max_downloads != -1) & (Transfer.current_downloads >= Transfer.max_downloads))
            ) &
            (Transfer.status != 'expired')
        ).all()

        for transfer in expired:
            try:
                await self.storage.delete_file(transfer.storage_key)

                # 更新配额
                system_config = db.query(SystemConfig).first()
                system_config.server_current_bytes -= transfer.file_size

                tkn = db.query(Token).filter(Token.user_id == transfer.owner_id).first()
                if tkn and tkn.quota_current_size >= transfer.file_size:
                    tkn.quota_current_size -= transfer.file_size

                transfer.status = 'expired'

            except Exception as e:
                pass  # Continue on error

        db.commit()
        db.close()

    async def check_disk_space(self):
        """检查磁盘空间，必要时强制清理"""
        db = get_db_session()

        system_config = db.query(SystemConfig).first()

        # 检查是否接近服务器配额
        if system_config.server_current_bytes > system_config.server_quota_bytes * 0.9:
            # 按过期时间排序，优先清理即将过期的
            transfers = db.query(Transfer).filter(
                Transfer.status == 'active'
            ).order_by(Transfer.expire_at.asc()).all()

            freed_bytes = 0
            target_bytes = system_config.server_quota_bytes * 0.8

            for transfer in transfers:
                try:
                    await self.storage.delete_file(transfer.storage_key)

                    # 更新配额
                    system_config.server_current_bytes -= transfer.file_size
                    tkn = db.query(Token).filter(Token.user_id == transfer.owner_id).first()
                    if tkn and tkn.quota_current_size >= transfer.file_size:
                        tkn.quota_current_size -= transfer.file_size

                    transfer.status = 'revoked'
                    freed_bytes += transfer.file_size

                    if system_config.server_current_bytes <= target_bytes:
                        break

                except Exception as e:
                    pass  # Continue on error

            db.commit()

        db.close()


def start_janitor(config: dict, storage_backend):
    """启动 Janitor 线程"""
    janitor = FileJanitor(config, storage_backend)

    import threading
    thread = threading.Thread(
        target=lambda: asyncio.run(janitor.start()),
        daemon=True
    )
    thread.start()

    return janitor
