"""
filetrans database connection and session management
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from .models import Base


# 数据库配置
DEFAULT_DB_PATH = "./data/filetrans.db"


def get_db_path() -> str:
    """获取数据库文件路径"""
    db_path = os.environ.get('FT_DB_PATH', DEFAULT_DB_PATH)
    # 确保目录存在
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return db_path


def get_engine():
    """获取数据库引擎"""
    db_path = get_db_path()
    return create_engine(f"sqlite:///{db_path}", echo=False)


def init_db():
    """初始化数据库"""
    engine = get_engine_global()

    # 确保所有表被创建
    from .models import SystemConfig, Token, Transfer, DownloadLog, Webhook
    Base.metadata.create_all(bind=engine)

    # 初始化系统配置
    SessionMaker = get_session_maker()
    db = SessionMaker()

    existing = db.query(SystemConfig).first()
    if not existing:
        # 从环境变量解析配额大小
        server_quota = os.environ.get('FT_SERVER_QUOTA', '100GB')
        try:
            quota_bytes = _parse_size(server_quota)
        except:
            quota_bytes = 100 * 1024 * 1024 * 1024  # 默认 100GB

        config = SystemConfig(
            id=1,
            server_quota_bytes=quota_bytes,
            storage_backend=os.environ.get('FT_STORAGE', 'LOCAL'),
            janitor_interval_seconds=int(os.environ.get('FT_CLEANUP_INTERVAL', 60)),
            max_file_size=int(os.environ.get('FT_MAX_SIZE', 512 * 1024 * 1024))
        )
        db.add(config)
        db.commit()

    db.close()


# 全局引擎
_engine = None
SessionLocal = None


def get_engine_global():
    """获取全局数据库引擎"""
    global _engine
    if _engine is None:
        _engine = get_engine()
    return _engine


def get_session_maker():
    """获取 SessionMaker"""
    global SessionLocal
    if SessionLocal is None:
        engine = get_engine_global()
        SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return SessionLocal


def _parse_size(size_str: str) -> int:
    """解析大小字符串"""
    size_str = str(size_str).strip().upper()
    match = __import__('re').match(r'([\d.]+)([KMGT]?B?)', size_str)
    if match:
        value = float(match.group(1))
        unit = match.group(2)
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024**2,
            'GB': 1024**3,
            'TB': 1024**4
        }
        return int(value * multipliers.get(unit, 1))
    return int(size_str)


@contextmanager
def get_db():
    """获取数据库会话（上下文管理器）"""
    SessionMaker = get_session_maker()
    db = SessionMaker()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """获取数据库会话（直接返回）"""
    SessionMaker = get_session_maker()
    return SessionMaker()
