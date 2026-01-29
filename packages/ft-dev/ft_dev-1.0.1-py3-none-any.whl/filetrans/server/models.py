"""
filetrans database models
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, Text, ForeignKey, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class SystemConfig(Base):
    """系统配置表（单行）"""
    __tablename__ = 'system_config'

    id = Column(Integer, primary_key=True, default=1)
    server_quota_bytes = Column(BigInteger, default=100 * 1024 * 1024 * 1024)  # 100GB
    server_current_bytes = Column(BigInteger, default=0)
    storage_backend = Column(String(10), default='LOCAL')
    janitor_interval_seconds = Column(Integer, default=60)
    max_file_size = Column(BigInteger, default=512 * 1024 * 1024)  # 512MB
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('id = 1', name='check_single_row'),
    )


class Token(Base):
    """API Token 表"""
    __tablename__ = 'tokens'

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    label = Column(String(100))
    permissions = Column(Text)  # JSON 存储
    quota_max_size = Column(BigInteger, default=10 * 1024 * 1024 * 1024)  # 10GB
    quota_current_size = Column(BigInteger, default=0)
    max_file_size = Column(BigInteger, default=512 * 1024 * 1024)  # 512MB
    rate_limit_rps = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)  # 管理员标记
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)


class Transfer(Base):
    """文件传输记录表"""
    __tablename__ = 'transfers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    owner_id = Column(String(50), nullable=False, index=True)
    group_name = Column(String(50), default='default', index=True)

    # 文件信息
    file_name = Column(Text, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100))
    file_hash = Column(String(64))

    # 存储信息
    storage_mode = Column(String(10), nullable=False)  # 'S3' or 'LOCAL'
    storage_key = Column(Text, nullable=False)

    # 安全信息
    pwd_hash = Column(String)
    is_e2ee = Column(Boolean, default=False)
    is_public = Column(Boolean, default=True, index=True)  # 共享模式

    # 生命周期
    status = Column(String(20), default='pending')  # pending, active, expired, revoked
    created_at = Column(DateTime, default=func.now())
    expire_at = Column(DateTime, nullable=False, index=True)
    max_downloads = Column(Integer, default=-1)
    current_downloads = Column(Integer, default=0)

    # 元数据
    upload_ip = Column(String(45))
    user_agent = Column(Text)


class DownloadLog(Base):
    """下载日志表"""
    __tablename__ = 'download_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    transfer_code = Column(String(10), nullable=False, index=True)
    downloaded_at = Column(DateTime, default=func.now(), index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    success = Column(Boolean, default=True)


class Webhook(Base):
    """Webhook 配置表"""
    __tablename__ = 'webhooks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(String(50), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # download, expire, upload
    url = Column(Text, nullable=False)
    secret = Column(String(64))
    is_active = Column(Boolean, default=True)


class Clipboard(Base):
    """用户剪贴板表"""
    __tablename__ = 'clipboards'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, index=True)

    # 内容类型: 'text' 或 'file'
    content_type = Column(String(10), nullable=False)  # 'text' or 'file'

    # 文本内容（当 content_type='text' 时使用）
    text_content = Column(Text, nullable=True)

    # 文件引用（当 content_type='file' 时使用）
    file_code = Column(String(10), nullable=True)

    # 元数据
    filename = Column(Text, nullable=True)  # 原始文件名或描述
    size = Column(BigInteger, default=0)

    created_at = Column(DateTime, default=func.now(), index=True)

    __table_args__ = (
        CheckConstraint("content_type IN ('text', 'file')", name='check_content_type'),
    )
