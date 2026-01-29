# `filetrans` (ft) 全栈开发指导手册 v1.0

## 目录

- [1. 项目定位](#1-项目定位)
- [2. 核心技术栈](#2-核心技术栈)
- [3. 系统架构](#3-系统架构)
- [4. 数据库 Schema](#4-数据库-schema)
- [5. 服务端详细设计](#5-服务端详细设计)
- [6. API 完全规格 (jRPC)](#6-api-完全规格-jrpc)
- [7. CLI 详细设计](#7-cli-详细设计)
- [8. Web 管理端设计](#8-web-管理端设计)
- [9. 自动化清理机制](#9-自动化清理机制)
- [10. 工程化发布指导](#10-工程化发布指导)
- [11. 增强版功能矩阵](#11-增强版功能矩阵)
- [12. 下一步开发方向](#12-下一步开发方向)

---

## 1. 项目定位

### 1.1 核心理念

**`filetrans` (简称 `ft`)** 是一个现代化的文件传输工具，采用"哑客户端 + 智能服务端 + 灵活存储后端"的架构设计。

### 1.2 工作流程

```
┌─────────────┐      jRPC       ┌─────────────┐     Presigned URL     ┌─────────────┐
│   CLI 客户端  │ ──────────────> │   服务端      │ ──────────────────> │  存储后端     │
│  (ft -p)    │ <────────────── │  (FastAPI)  │ <────────────────── │  (S3/Local) │
└─────────────┘   Code + URL   └─────────────┘    Upload Success    └─────────────┘
       │                             │                                    │
       │                             ├────────────────────────────────────┤
       │                             │  元数据维护 (SQLite)                │
       ▼                             ▼                                    ▼
  ┌─────────────┐              ┌─────────────┐                    ┌─────────────┐
  │ 打印 Code   │              │  Web 预览    │                    │  物理文件     │
  │ 分享链接    │              │  /g/<code>  │                    │  按需清理     │
  └─────────────┘              └─────────────┘                    └─────────────┘
```

### 1.3 设计目标

| 目标 | 说明 |
|------|------|
| **简单性** | 客户端只需一个命令完成上传/下载 |
| **安全性** | 支持 Token 认证、密码保护、端到端加密 |
| **可扩展性** | 支持多种存储后端（S3、Local、未来可扩展） |
| **可管理性** | 提供完整的 Web 管理后台和 API |
| **共享性** | 支持服务器内文件共享（Public/Private 模式） |

### 1.4 共享模式说明

| 模式 | 说明 |
|------|------|
| **`-public`** (默认) | 同服务器内所有用户可见（通过 `ft ls` 可列出） |
| **`-private`** | 仅上传者可见 |

> **注意**：无论 Public/Private，所有文件都可以通过 Code 下载。Public 模式只是让其他用户能在 `ft ls` 中看到。

---

## 2. 核心技术栈

### 2.1 技术选型总览

```
┌─────────────────────────────────────────────────────────────────────┐
│                         filetrans 技术栈                            │
├─────────────┬─────────────┬─────────────┬───────────────────────────┤
│    CLI      │   Backend   │  Database   │       Storage            │
├─────────────┼─────────────┼─────────────┼───────────────────────────┤
│  Typer      │  FastAPI    │  SQLite     │  S3 (via Boto3)          │
│  Rich       │  Uvicorn    │  SQLAlchemy │  Local Filesystem        │
│  Requests   │  jRPC 2.0   │  Alembic?   │  (未来: MinIO, Azure)    │
│  Pyclip     │  Pydantic   │             │                           │
└─────────────┴─────────────┴─────────────┴───────────────────────────┘
```

### 2.2 详细依赖说明

#### 2.2.1 CLI 客户端

| 依赖 | 版本要求 | 用途 |
|------|---------|------|
| `typer[all]` | ≥0.9.0 | 命令行参数解析、子命令管理 |
| `rich` | ≥13.0.0 | 进度条、表格输出、终端美化 |
| `requests` | ≥2.28.0 | HTTP 客户端，与 jRPC 服务端通信 |
| `pyclip` | ≥0.7.0 | 跨平台剪贴板操作 |

#### 2.2.2 服务端

| 依赖 | 版本要求 | 用途 |
|------|---------|------|
| `fastapi` | ≥0.100.0 | Web 框架，提供 jRPC 路由 |
| `uvicorn[standard]` | ≥0.23.0 | ASGI 服务器 |
| `pydantic` | ≥2.0.0 | 数据验证与序列化 |
| `sqlalchemy` | ≥2.0.0 | ORM，数据库抽象层 |
| `boto3` | ≥1.28.0 | AWS S3 SDK |

#### 2.2.3 Web 前端

| 技术 | 说明 |
|------|------|
| 原生 HTML/CSS/JS | 无构建工具依赖 |
| Tailwind CSS (CDN) | 快速样式开发 |
| Axios (CDN) | AJAX 请求 |
| Chart.js (CDN) | Dashboard 图表 |

---

## 3. 系统架构

### 3.1 目录结构

```
filetrans/
├── filetrans/
│   ├── __init__.py
│   ├── cli.py                 # Typer CLI 入口
│   ├── client/
│   │   ├── __init__.py
│   │   ├── api.py             # jRPC 客户端封装
│   │   ├── upload.py          # 上传逻辑
│   │   ├── download.py        # 下载逻辑
│   │   └── clipboard.py       # 剪贴板处理
│   ├── server/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI 应用入口
│   │   ├── jrpc.py            # jRPC 方法注册与处理
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   ├── base.py        # Storage 抽象基类
│   │   │   ├── s3.py          # S3 实现
│   │   │   └── local.py       # Local 实现
│   │   ├── models.py          # SQLAlchemy 模型
│   │   ├── database.py        # 数据库连接管理
│   │   ├── janitor.py         # 后台清理任务
│   │   └── config.py          # 配置管理
│   └── web/
│       ├── __init__.py
│       ├── templates/
│       │   ├── base.html
│       │   ├── download.html  # /g/<code> 下载页面
│       │   └── admin.html     # 管理后台 SPA
│       └── static/
│           └── css/
│           └── js/
├── tests/
│   ├── __init__.py
│   ├── test_client.py
│   ├── test_server.py
│   └── conftest.py
├── migrations/                # Alembic 迁移文件（如使用）
├── pyproject.toml
├── README.md
└── .env.example
```

### 3.2 配置文件

#### 3.2.1 CLI 客户端配置 (`~/.config/filetrans/config.json`)

```json
{
  "server_url": "https://filetrans.example.com",
  "api_token": "ft_xxxxxxxxxxxxxxxxxxxx",
  "default_ttl": "24h",
  "default_group": "default"
}
```

#### 3.2.2 服务端配置 (`config.yaml` 或环境变量)

```yaml
server:
  host: "0.0.0.0"
  port: 8866
  workers: 4

database:
  url: "sqlite:///./filetrans.db"

storage:
  backend: "s3"  # or "local"
  local:
    root_dir: "./data/files"
  s3:
    bucket: "filetrans-bucket"
    region: "us-east-1"
    endpoint_url: "https://s3.amazonaws.com"

security:
  jwt_secret: "CHANGE_ME_IN_PRODUCTION"
  token_length: 32

janitor:
  interval_seconds: 60
  disk_threshold_percent: 10
```

---

## 4. 数据库 Schema

### 4.1 完整表结构

```sql
-- ==================================================
-- filetrans Database Schema v1.1
-- ==================================================

-- 系统配置表 (单行)
CREATE TABLE system_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    server_quota_bytes INTEGER DEFAULT 107374182400,  -- 100GB 服务器默认配额
    server_current_bytes INTEGER DEFAULT 0,            -- 当前使用量
    storage_backend VARCHAR(10) DEFAULT 'LOCAL',        -- 'S3' or 'LOCAL'
    janitor_interval_seconds INTEGER DEFAULT 60,
    max_file_size INTEGER DEFAULT 536870912,           -- 单文件最大 512MB
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 用户/API Token 表
CREATE TABLE tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token VARCHAR(64) UNIQUE NOT NULL,           -- API Token (ft_xxx...)
    user_id VARCHAR(50) NOT NULL,                -- 用户标识
    label VARCHAR(100),                          -- Token 描述 (如 "iPhone Token")
    permissions TEXT,                            -- JSON: ["read", "write", "admin"]
    quota_max_size INTEGER DEFAULT 10737418240,  -- 10GB 默认配额
    quota_current_size INTEGER DEFAULT 0,        -- 当前使用量
    max_file_size INTEGER DEFAULT 536870912,     -- 单文件最大 512MB
    rate_limit_rps INTEGER DEFAULT 10,           -- 每秒请求限制
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    INDEX idx_token (token),
    INDEX idx_user_id (user_id)
);

-- 文件传输记录表 (核心表)
CREATE TABLE transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(10) UNIQUE NOT NULL,            -- 4-6 位短码 (下载提取码)
    owner_id VARCHAR(50) NOT NULL,               -- 关联 tokens.user_id
    group_name VARCHAR(50) DEFAULT 'default',    -- 命名空间/分组

    -- 文件信息
    file_name TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100),
    file_hash VARCHAR(64),                       -- SHA-256

    -- 存储信息
    storage_mode VARCHAR(10) NOT NULL,           -- 'S3' or 'LOCAL'
    storage_key TEXT NOT NULL,                   -- S3 Key 或本地相对路径

    -- 安全信息
    pwd_hash TEXT,                               -- bcrypt 密码哈希 (可为 NULL)
    is_e2ee BOOLEAN DEFAULT FALSE,               -- 端到端加密标记
    is_public BOOLEAN DEFAULT TRUE,              -- 共享模式: public=服务器内可见, private=仅自己可见

    -- 生命周期控制
    status VARCHAR(20) DEFAULT 'pending',        -- pending, active, expired, revoked
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expire_at DATETIME NOT NULL,
    max_downloads INTEGER DEFAULT -1,            -- -1 = 无限制
    current_downloads INTEGER DEFAULT 0,

    -- 元数据
    upload_ip VARCHAR(45),                       -- 支持 IPv6
    user_agent TEXT,

    INDEX idx_code (code),
    INDEX idx_owner (owner_id),
    INDEX idx_status (status),
    INDEX idx_expire (expire_at),
    INDEX idx_group (group_name),
    INDEX idx_public (is_public),                 -- 用于快速查询公开文件
    FOREIGN KEY (owner_id) REFERENCES tokens(user_id) ON DELETE CASCADE
);

-- 下载日志表
CREATE TABLE download_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transfer_code VARCHAR(10) NOT NULL,
    downloaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    success BOOLEAN DEFAULT TRUE,
    INDEX idx_code (transfer_code),
    INDEX idx_time (downloaded_at),
    FOREIGN KEY (transfer_code) REFERENCES transfers(code) ON DELETE CASCADE
);

-- Webhook 配置表
CREATE TABLE webhooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,             -- 'download', 'expire', 'upload'
    url TEXT NOT NULL,
    secret VARCHAR(64),                          -- HMAC 签名密钥
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_owner (owner_id),
    INDEX idx_event (event_type)
);
```

### 4.2 SQLAlchemy 模型定义

```python
# filetrans/server/models.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, Text, ForeignKey, Index, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

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
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)

class Transfer(Base):
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
    __tablename__ = 'download_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    transfer_code = Column(String(10), nullable=False, index=True)
    downloaded_at = Column(DateTime, default=func.now(), index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    success = Column(Boolean, default=True)

class Webhook(Base):
    __tablename__ = 'webhooks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(String(50), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # download, expire, upload
    url = Column(Text, nullable=False)
    secret = Column(String(64))
    is_active = Column(Boolean, default=True)
```

---

## 5. 服务端详细设计

### 5.1 存储目录隔离策略

#### 5.1.1 设计原则

| 原则 | 说明 |
|------|------|
| **用户隔离** | 每个 Token 的文件存储在独立的用户目录下 |
| **不可变路径** | 存储路径生成后不再更改，便于追踪 |
| **可预测性** | 支持从 Code 反推存储路径（便于调试） |

#### 5.1.2 路径生成规则

**S3 模式**:
```
s3://{bucket}/{user_id}/{code}_{uuid[:8]}/{filename}
```

**Local 模式**:
```
{STORAGE_ROOT}/{user_id}/{code}/{filename}
```

#### 5.1.3 代码实现

```python
# filetrans/server/storage/base.py

from abc import ABC, abstractmethod
from typing import Tuple, Optional
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
```

### 5.2 jRPC 方法注册

```python
# filetrans/server/jrpc.py

from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
import bcrypt

from .database import get_db
from .models import Transfer, Token
from .storage.base import StorageBackend

router = APIRouter()

# ==================================================
# Pydantic 模型定义
# ==================================================

class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: dict = {}
    id: Optional[str] = None

class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Optional[dict] = None
    error: Optional[dict] = None
    id: Optional[str] = None

class InitUploadParams(BaseModel):
    filename: str = Field(..., description="原始文件名")
    filesize: int = Field(..., gt=0, description="文件大小（字节）")
    ttl: int = Field(default=86400, ge=60, le=2592000, description="过期秒数")
    download_limit: int = Field(default=-1, ge=-1, description="下载次数限制")
    has_password: bool = Field(default=False, description="是否设置下载密码")
    e2ee: bool = Field(default=False, description="是否端到端加密")
    password: Optional[str] = Field(None, description="下载密码（如果 has_password=True）")
    is_public: bool = Field(default=True, description="是否公开（同服务器内可见）")
    group: str = Field(default="default", description="命名空间")
    file_hash: Optional[str] = Field(None, description="文件 SHA-256 哈希")

class VerifyAndGetLinkParams(BaseModel):
    code: str = Field(..., min_length=4, max_length=10)
    password: Optional[str] = None

# ==================================================
# 依赖项：Token 认证
# ==================================================

async def verify_token(authorization: str = Header(...), db = Depends(get_db)) -> Token:
    """验证 API Token 并返回 Token 对象"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token_str = authorization[7:]  # Remove "Bearer "
    token = db.query(Token).filter(Token.token == token_str, Token.is_active == True).first()

    if not token:
        raise HTTPException(status_code=401, detail="Invalid or inactive token")

    if token.expires_at and token.expires_at < datetime.now():
        raise HTTPException(status_code=401, detail="Token expired")

    return token

# ==================================================
# jRPC 方法实现
# ==================================================

@router.post("/jrpc")
async def jsonrpc_handler(
    request: JSONRPCRequest,
    token: Token = Depends(verify_token),
    storage: StorageBackend = Depends(get_storage),
    db = Depends(get_db)
):
    """jRPC 2.0 请求分发器"""

    methods = {
        "ft.init_upload": handle_init_upload,
        "ft.confirm_upload": handle_confirm_upload,
        "ft.fetch_metadata": handle_fetch_metadata,
        "ft.verify_and_get_link": handle_verify_and_get_link,
        "ft.list_my_files": handle_list_my_files,
        "admin.list_all": handle_admin_list_all,
        "admin.revoke_code": handle_admin_revoke_code,
        "admin.manage_token": handle_admin_manage_token,
        "admin.get_stats": handle_admin_get_stats,
    }

    handler = methods.get(request.method)
    if not handler:
        return JSONRPCResponse(
            id=request.id,
            error={"code": -32601, "message": "Method not found"}
        )

    try:
        result = await handler(request.params, token, storage, db)
        return JSONRPCResponse(id=request.id, result=result)
    except Exception as e:
        return JSONRPCResponse(
            id=request.id,
            error={"code": -32603, "message": str(e)}
        )

# ==================================================
# 核心方法实现
# ==================================================

async def handle_init_upload(
    params: dict,
    token: Token,
    storage: StorageBackend,
    db
) -> dict:
    """初始化上传任务"""

    # 1. 参数验证
    p = InitUploadParams(**params)

    # 2. 检查配额
    if token.quota_current_size + p.filesize > token.quota_max_size:
        raise ValueError("Quota exceeded")

    if p.filesize > token.max_file_size:
        raise ValueError(f"File size exceeds limit of {token.max_file_size} bytes")

    # 3. 生成唯一 Code
    import random
    import string
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    # 4. 生成存储 Key 和预签名 URL
    storage_key = storage.generate_storage_key(token.user_id, code, p.filename)
    upload_url, storage_key = await storage.generate_upload_url(
        user_id=token.user_id,
        code=code,
        filename=p.filename,
        ttl_seconds=p.ttl
    )

    # 5. 计算密码哈希（如果需要）
    pwd_hash = None
    if p.has_password and p.password:
        pwd_hash = bcrypt.hashpw(p.password.encode(), bcrypt.gensalt()).decode()

    # 6. 创建数据库记录
    from datetime import datetime, timedelta
    transfer = Transfer(
        code=code,
        owner_id=token.user_id,
        group_name=p.group,
        file_name=p.filename,
        file_size=p.filesize,
        mime_type=_guess_mime_type(p.filename),
        file_hash=p.file_hash,
        storage_mode=storage.config['backend'].upper(),
        storage_key=storage_key,
        pwd_hash=pwd_hash,
        is_e2ee=p.e2ee,
        status='pending',
        expire_at=datetime.now() + timedelta(seconds=p.ttl),
        max_downloads=p.download_limit
    )
    db.add(transfer)
    db.commit()

    return {
        "code": code,
        "mode": storage.config['backend'].upper(),
        "upload_url": upload_url,
        "view_url": f"{storage.config['base_url']}/g/{code}"
    }

async def handle_confirm_upload(params: dict, token: Token, storage: StorageBackend, db) -> dict:
    """客户端上传成功后的回调"""
    code = params['code']
    status = params.get('status', 'success')

    transfer = db.query(Transfer).filter(Transfer.code == code).first()
    if not transfer:
        raise ValueError("Transfer not found")

    if status == 'success':
        transfer.status = 'active'
        # 更新用户配额
        tkn = db.query(Token).filter(Token.user_id == transfer.owner_id).first()
        if tkn:
            tkn.quota_current_size += transfer.file_size
    else:
        transfer.status = 'failed'
        # 清理已上传的文件
        await storage.delete_file(transfer.storage_key)

    db.commit()
    return {"success": True}

async def handle_fetch_metadata(params: dict, token: Token, storage: StorageBackend, db) -> dict:
    """获取文件元数据"""
    code = params['code']
    transfer = db.query(Transfer).filter(Transfer.code == code).first()

    if not transfer:
        raise ValueError("Transfer not found")

    return {
        "filename": transfer.file_name,
        "size": transfer.file_size,
        "has_password": transfer.pwd_hash is not None,
        "e2ee_status": transfer.is_e2ee,
        "mime_type": transfer.mime_type,
        "created_at": transfer.created_at.isoformat(),
        "expire_at": transfer.expire_at.isoformat()
    }

async def handle_verify_and_get_link(params: dict, token: Token, storage: StorageBackend, db) -> dict:
    """验证密码并获取下载链接"""
    p = VerifyAndGetLinkParams(**params)
    transfer = db.query(Transfer).filter(Transfer.code == p.code).first()

    if not transfer:
        raise ValueError("Transfer not found")

    # 检查状态
    if transfer.status != 'active':
        raise ValueError(f"Transfer is {transfer.status}")

    # 检查过期
    if transfer.expire_at < datetime.now():
        transfer.status = 'expired'
        db.commit()
        raise ValueError("Transfer has expired")

    # 检查下载次数
    if transfer.max_downloads != -1 and transfer.current_downloads >= transfer.max_downloads:
        raise ValueError("Download limit exceeded")

    # 验证密码
    if transfer.pwd_hash:
        if not p.password:
            return {"need_password": True}
        if not bcrypt.checkpw(p.password.encode(), transfer.pwd_hash.encode()):
            raise ValueError("Invalid password")

    # 生成下载链接
    download_url = await storage.generate_download_url(
        storage_key=transfer.storage_key,
        ttl_seconds=3600  # 1 小时有效期
    )

    # 更新下载计数
    transfer.current_downloads += 1
    db.commit()

    return {
        "download_url": download_url,
        "filename": transfer.file_name
    }

async def handle_list_my_files(params: dict, token: Token, storage: StorageBackend, db) -> dict:
    """列出文件（支持 public 模式）"""
    page = params.get('page', 1)
    page_size = params.get('page_size', 20)
    include_public = params.get('include_public', True)  # 默认包含公开文件

    # 查询逻辑：自己的所有文件 + 其他用户的公开文件
    from sqlalchemy import or_

    if include_public:
        query = db.query(Transfer).filter(
            or_(
                Transfer.owner_id == token.user_id,
                Transfer.is_public == True
            )
        )
    else:
        query = db.query(Transfer).filter(Transfer.owner_id == token.user_id)

    # 只显示活跃的文件
    query = query.filter(Transfer.status == 'active')

    query = query.order_by(Transfer.created_at.desc())
    total = query.count()
    transfers = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "files": [
            {
                "code": t.code,
                "filename": t.file_name,
                "size": t.file_size,
                "owner": t.owner_id,
                "is_mine": t.owner_id == token.user_id,
                "is_public": t.is_public,
                "created_at": t.created_at.isoformat(),
                "expire_at": t.expire_at.isoformat(),
                "downloads": f"{t.current_downloads}/{t.max_downloads if t.max_downloads != -1 else '∞'}",
                "status": t.status
            }
            for t in transfers
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }

# ==================================================
# 管理员方法
# ==================================================

async def handle_admin_list_all(params: dict, token: Token, storage: StorageBackend, db) -> dict:
    """管理员：列出所有文件"""
    # 检查权限
    if "admin" not in token.permissions:
        raise ValueError("Admin permission required")

    filter_status = params.get('filter_status')
    group = params.get('group')

    query = db.query(Transfer)
    if filter_status:
        query = query.filter(Transfer.status == filter_status)
    if group:
        query = query.filter(Transfer.group_name == group)

    transfers = query.all()
    return {
        "files": [
            {
                "code": t.code,
                "owner": t.owner_id,
                "filename": t.file_name,
                "size": t.file_size,
                "status": t.status,
                "expire_at": t.expire_at.isoformat()
            }
            for t in transfers
        ]
    }

async def handle_admin_revoke_code(params: dict, token: Token, storage: StorageBackend, db) -> dict:
    """管理员：强制撤销 Code"""
    if "admin" not in token.permissions:
        raise ValueError("Admin permission required")

    code = params['code']
    transfer = db.query(Transfer).filter(Transfer.code == code).first()

    if not transfer:
        raise ValueError("Transfer not found")

    # 物理删除
    await storage.delete_file(transfer.storage_key)
    db.delete(transfer)
    db.commit()

    return {"status": "revoked"}

async def handle_admin_manage_token(params: dict, token: Token, storage: StorageBackend, db) -> dict:
    """管理员：管理 API Token"""
    if "admin" not in token.permissions:
        raise ValueError("Admin permission required")

    action = params['action']
    config = params.get('config', {})

    if action == 'add':
        # 生成新 Token
        import secrets
        new_token = f"ft_{secrets.token_urlsafe(32)}"
        db_token = Token(
            token=new_token,
            user_id=config.get('user_id', 'unknown'),
            label=config.get('label', ''),
            permissions=config.get('permissions', ['read', 'write']),
            quota_max_size=config.get('quota_max_size', 10 * 1024 * 1024 * 1024)
        )
        db.add(db_token)
        db.commit()
        return {"token": new_token, "status": "created"}

    elif action == 'revoke':
        token_str = config['token']
        db_token = db.query(Token).filter(Token.token == token_str).first()
        if db_token:
            db_token.is_active = False
            db.commit()
        return {"status": "revoked"}

    return {"status": "unknown_action"}

async def handle_admin_get_stats(params: dict, token: Token, storage: StorageBackend, db) -> dict:
    """管理员：获取统计信息"""
    if "admin" not in token.permissions:
        raise ValueError("Admin permission required")

    from sqlalchemy import func

    total_files = db.query(func.count(Transfer.id)).scalar()
    total_size = db.query(func.sum(Transfer.file_size)).scalar() or 0
    active_files = db.query(func.count(Transfer.id)).filter(Transfer.status == 'active').scalar()

    return {
        "total_files": total_files,
        "active_files": active_files,
        "total_storage_bytes": total_size,
        "storage_backend": storage.config['backend']
    }

# ==================================================
# 辅助函数
# ==================================================

def _guess_mime_type(filename: str) -> str:
    """简单 MIME 类型检测"""
    import mimetypes
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'
```

### 5.3 FastAPI 主入口

```python
# filetrans/server/main.py

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn

from .jrpc import router as jrpc_router
from .janitor import start_janitor
from .config import load_config

config = load_config()

app = FastAPI(
    title="filetrans",
    description="Modern file transfer service with jRPC API",
    version="1.0.0"
)

# 挂载 jRPC 路由
app.include_router(jrpc_router, prefix="/api")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="filetrans/web/static"), name="static")

# 模板
templates = Jinja2Templates(directory="filetrans/web/templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首页"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/g/{code}", response_class=HTMLResponse)
async def download_page(request: Request, code: str):
    """下载页面"""
    return templates.TemplateResponse("download.html", {"request": request, "code": code})

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """管理后台"""
    return templates.TemplateResponse("admin.html", {"request": request})

@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    # 启动清理任务
    start_janitor(config)

def serve():
    """启动服务器"""
    uvicorn.run(
        "filetrans.server.main:app",
        host=config['server']['host'],
        port=config['server']['port'],
        workers=config['server'].get('workers', 1)
    )
```

---

## 6. API 完全规格 (jRPC)

### 6.1 通信协议

#### 6.1.1 请求格式

```json
{
  "jsonrpc": "2.0",
  "method": "ft.init_upload",
  "params": {
    "filename": "document.pdf",
    "filesize": 1048576,
    "ttl": 86400,
    "download_limit": 5,
    "has_password": true,
    "password": "secret123",
    "e2ee": false,
    "group": "default"
  },
  "id": "1"
}
```

#### 6.1.2 响应格式（成功）

```json
{
  "jsonrpc": "2.0",
  "result": {
    "code": "A3F9K2",
    "mode": "S3",
    "upload_url": "https://s3.amazonaws.com/bucket/user123/A3F9K2/document.pdf?signature=...",
    "view_url": "https://filetrans.example.com/g/A3F9K2"
  },
  "id": "1"
}
```

#### 6.1.3 响应格式（错误）

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid params: filesize exceeds quota",
    "data": {
      "field": "filesize",
      "limit": 536870912,
      "provided": 1073741824
    }
  },
  "id": "1"
}
```

### 6.2 API 方法完整列表

#### 6.2.1 用户方法

| 方法 | 权限 | 说明 |
|------|------|------|
| `ft.init_upload` | write | 初始化上传任务 |
| `ft.confirm_upload` | write | 确认上传完成 |
| `ft.fetch_metadata` | read | 获取文件元数据 |
| `ft.verify_and_get_link` | read | 验证密码并获取下载链接 |
| `ft.list_my_files` | read | 列出当前用户的文件 |

#### 6.2.2 管理员方法

| 方法 | 权限 | 说明 |
|------|------|------|
| `admin.list_all` | admin | 列出所有文件 |
| `admin.revoke_code` | admin | 撤销指定 Code |
| `admin.manage_token` | admin | 管理 API Token |
| `admin.get_stats` | admin | 获取系统统计 |

### 6.3 错误码规范

| 错误码 | 名称 | 说明 |
|--------|------|------|
| -32700 | Parse error | JSON 解析错误 |
| -32600 | Invalid Request | 无效的 jRPC 请求 |
| -32601 | Method not found | 方法不存在 |
| -32602 | Invalid params | 参数验证失败 |
| -32603 | Internal error | 服务器内部错误 |
| 401 | Unauthorized | Token 无效或过期 |
| 403 | Forbidden | 权限不足 |
| 404 | Not found | 资源不存在 |
| 429 | Too many requests | 超出速率限制 |

### 6.4 jRPC 请求示例

#### 示例 1：初始化上传

```bash
curl -X POST https://filetrans.example.com/api/jrpc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ft_your_token_here" \
  -d '{
    "jsonrpc": "2.0",
    "method": "ft.init_upload",
    "params": {
      "filename": "presentation.pptx",
      "filesize": 5242880,
      "ttl": 604800,
      "download_limit": 10,
      "has_password": true,
      "password": "secure456",
      "e2ee": false
    },
    "id": "req-001"
  }'
```

#### 示例 2：获取下载链接

```bash
curl -X POST https://filetrans.example.com/api/jrpc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ft_your_token_here" \
  -d '{
    "jsonrpc": "2.0",
    "method": "ft.verify_and_get_link",
    "params": {
      "code": "A3F9K2",
      "password": "secure456"
    },
    "id": "req-002"
  }'
```

---

## 7. CLI 详细设计

### 7.1 命令结构

```
ft
├── init                    # 初始化配置
├── -p, --push [PATH]       # 上传文件
├── -g, --get [CODE]        # 下载文件
├── ls                      # 列出文件
├── serve                   # 启动服务器
├── token                   # Token 管理
└── --version               # 版本信息
```

### 7.2 完整实现

```python
# filetrans/cli.py

import typer
import requests
import rch
from pathlib import Path
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TimeRemainingColumn
from rich.console import Console
from rich.table import Table
import configparser
import os
from .client.api import FiletransClient

app = typer.Typer(name="ft", help="filetrans - Modern file transfer tool")
console = Console()

CONFIG_DIR = Path.home() / ".config" / "filetrans"
CONFIG_FILE = CONFIG_DIR / "config.json"

# ==================================================
# 初始化命令
# ==================================================

@app.command()
def init():
    """初始化 CLI 配置"""

    console.print("[bold blue]filetrans CLI 初始化向导[/bold blue]\n")

    server_url = typer.prompt("服务器 URL", default="https://filetrans.example.com")
    api_token = typer.prompt("API Token", hide_input=True)

    # 验证 Token
    with console.status("[bold yellow]验证 Token..."):
        client = FiletransClient(server_url, api_token)
        try:
            stats = client.call("admin.get_stats", {})
            console.print("[bold green]✓[/bold green] Token 验证成功")
        except Exception as e:
            console.print(f"[bold red]✗[/bold red] Token 验证失败: {e}")
            raise typer.Exit(1)

    # 创建配置目录
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # 写入配置
    import json
    config = {
        "server_url": server_url,
        "api_token": api_token
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

    # 设置权限
    os.chmod(CONFIG_FILE, 0o600)

    console.print(f"\n[bold green]配置已保存到:[/bold green] {CONFIG_FILE}")

# ==================================================
# 上传命令
# ==================================================

@app.command("-p")
@app.command("--push")
def push(
    path: str = typer.Argument(..., help="文件或目录路径"),
    ttl: str = typer.Option("24h", "--ttl", "-t", help="有效期（如 1h, 30m, 1d）"),
    limit: int = typer.Option(-1, "--limit", "-l", help="下载次数限制"),
    password: str = typer.Option(None, "--pass", "-P", help="下载密码"),
    encrypt: bool = typer.Option(False, "--encrypt", "-e", help="端到端加密"),
    public: bool = typer.Option(True, "--public/--private", help="是否公开（同服务器内可见）"),
    copy: bool = typer.Option(False, "--copy", "-c", help="复制到剪贴板"),
    group: str = typer.Option("default", "--group", help="命名空间"),
    silent: bool = typer.Option(False, "--silent", "-s", help="静默模式")
):
    """上传文件"""

    # 加载配置
    config = _load_config()
    client = FiletransClient(config['server_url'], config['api_token'])

    # 解析 TTL
    ttl_seconds = _parse_ttl(ttl)

    # 读取文件
    file_path = Path(path)
    if not file_path.exists():
        console.print(f"[bold red]错误:[/bold red] 文件不存在: {path}")
        raise typer.Exit(1)

    file_size = file_path.stat().st_size
    filename = file_path.name

    if not silent:
        console.print(f"[bold cyan]上传:[/bold cyan] {filename}")
        console.print(f"[bold cyan]大小:[/bold cyan] {humanize.naturalsize(file_size)}")

    # 读取文件内容
    with open(file_path, "rb") as f:
        file_data = f.read()

    # 计算 E2EE 加密（如果需要）
    if encrypt:
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
        cipher = Fernet(key)
        file_data = cipher.encrypt(file_data)
        console.print("[bold yellow]注意:[/bold yellow] 请妥善保管以下解密密钥:")
        console.print(f"[bold red]{key.decode()}[/bold red]\n")

    # 计算 SHA-256
    import hashlib
    file_hash = hashlib.sha256(file_data).hexdigest()

    # 初始化上传
    if not silent:
        with console.status("[bold yellow]初始化上传..."):
            result = client.call("ft.init_upload", {
                "filename": filename,
                "filesize": len(file_data),
                "ttl": ttl_seconds,
                "download_limit": limit,
                "has_password": password is not None,
                "password": password,
                "e2ee": encrypt,
                "is_public": public,
                "group": group,
                "file_hash": file_hash
            })
    else:
        result = client.call("ft.init_upload", {
            "filename": filename,
            "filesize": len(file_data),
            "ttl": ttl_seconds,
            "download_limit": limit,
            "has_password": password is not None,
            "password": password,
            "e2ee": encrypt,
            "is_public": public,
            "group": group,
            "file_hash": file_hash
        })

    code = result['code']
    upload_url = result['upload_url']
    view_url = result['view_url']

    # 上传文件
    if not silent:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]上传中...", total=len(file_data))

            response = requests.put(upload_url, data=file_data)
            progress.update(task, completed=len(file_data))
    else:
        response = requests.put(upload_url, data=file_data)

    if response.status_code not in [200, 201]:
        console.print(f"[bold red]上传失败:[/bold red] {response.status_code}")
        raise typer.Exit(1)

    # 确认上传
    client.call("ft.confirm_upload", {
        "code": code,
        "status": "success"
    })

    # 输出结果
    if not silent:
        console.print("\n[bold green]✓ 上传成功![/bold green]")
        console.print(f"[bold cyan]Code:[/bold cyan] {code}")
        console.print(f"[bold cyan]链接:[/bold cyan] {view_url}")
    else:
        console.print(code)

    # 复制到剪贴板
    if copy:
        import pyclip
        pyclip.copy(view_url)
        console.print("[bold green]已复制链接到剪贴板[/bold green]")

# ==================================================
# 下载命令
# ==================================================

@app.command("-g")
@app.command("--get")
def get(
    code: str = typer.Argument(..., help="提取码"),
    output: str = typer.Option(None, "--output", "-o", help="输出路径"),
    password: str = typer.Option(None, "--pass", "-P", help="下载密码"),
    copy: bool = typer.Option(False, "--copy", "-c", help="复制文本内容到剪贴板"),
    decrypt_key: str = typer.Option(None, "--decrypt-key", "-d", help="E2EE 解密密钥")
):
    """下载文件"""

    config = _load_config()
    client = FiletransClient(config['server_url'], config['api_token'])

    # 获取元数据
    metadata = client.call("ft.fetch_metadata", {"code": code})

    console.print(f"[bold cyan]文件:[/bold cyan] {metadata['filename']}")
    console.print(f"[bold cyan]大小:[/bold cyan] {humanize.naturalsize(metadata['size'])}")

    # 获取下载链接
    result = client.call("ft.verify_and_get_link", {
        "code": code,
        "password": password
    })

    if result.get("need_password"):
        password = typer.prompt("请输入密码", hide_input=True)
        result = client.call("ft.verify_and_get_link", {
            "code": code,
            "password": password
        })

    download_url = result['download_url']
    filename = result['filename']

    # 下载文件
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]下载中...", total=metadata['size'])

        response = requests.get(download_url, stream=True)
        file_data = b""
        for chunk in response.iter_content(chunk_size=8192):
            file_data += chunk
            progress.update(task, advance=len(chunk))

    # E2EE 解密
    if decrypt_key:
        from cryptography.fernet import Fernet
        cipher = Fernet(decrypt_key.encode())
        file_data = cipher.decrypt(file_data)

    # 输出
    output_path = Path(output) if output else Path.cwd() / filename

    if metadata['mime_type'].startswith('text/') and copy:
        import pyclip
        pyclip.copy(file_data.decode())
        console.print("[bold green]已复制文本内容到剪贴板[/bold green]")
    else:
        with open(output_path, "wb") as f:
            f.write(file_data)
        console.print(f"\n[bold green]✓ 已保存到:[/bold green] {output_path}")

# ==================================================
# 列表命令
# ==================================================

@app.command("ls")
def list_files(
    page: int = typer.Option(1, "--page", "-p", help="页码"),
    page_size: int = typer.Option(20, "--size", "-s", help="每页数量"),
    all: bool = typer.Option(False, "--all", "-a", help="显示所有文件（包括私有的）")
):
    """列出文件（公开 + 我的）"""

    config = _load_config()
    client = FiletransClient(config['server_url'], config['api_token'])

    result = client.call("ft.list_my_files", {
        "page": page,
        "page_size": page_size,
        "include_public": True  # 默认包含公开文件
    })

    table = Table(title=f"文件列表 {'(全部)' if all else '(公开 + 我的)'}")
    table.add_column("Code", style="cyan")
    table.add_column("文件名", style="white")
    table.add_column("所有者", style="magenta")
    table.add_column("可见性", style="bright_cyan")
    table.add_column("大小", style="green")
    table.add_column("过期时间", style="red")
    table.add_column("状态", style="yellow")

    for file in result['files']:
        # 过滤条件：all=True 显示全部，all=False 只显示公开的和自己的
        if not all and not file['is_public'] and not file['is_mine']:
            continue

        owner_display = "你" if file['is_mine'] else file['owner'][:8] + "..."
        visibility = "公开" if file['is_public'] else "私有"

        table.add_row(
            file['code'],
            file['filename'][:25] + "..." if len(file['filename']) > 25 else file['filename'],
            owner_display,
            visibility,
            humanize.naturalsize(file['size']),
            file['expire_at'][:10] if len(file['expire_at']) > 10 else file['expire_at'],
            file['status']
        )

    console.print(table)
    console.print(f"\n第 {page} 页，共 {result['total']} 个文件")

# ==================================================
# 服务器命令
# ==================================================

@app.command("serve")
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h"),
    port: int = typer.Option(8866, "--port", "-p"),
    storage: str = typer.Option("local", "--storage", "-s", help="存储类型 (local/s3)"),
    data_dir: str = typer.Option("./data", "--data-dir", "-d"),
    server_quota: str = typer.Option("100GB", "--server-quota", "-q", help="服务器总配额"),
    cleanup_interval: int = typer.Option(60, "--cleanup-interval"),
    max_size: int = typer.Option(536870912, "--max-size", help="单文件最大大小")
):
    """启动服务器（自动生成管理员 Token）"""

    from .server.main import serve as start_server

    console.print(f"[bold green]启动 filetrans 服务器...[/bold green]")
    console.print(f"[bold cyan]地址:[/bold cyan] http://{host}:{port}")
    console.print(f"[bold cyan]存储:[/bold cyan] {storage}")
    console.print(f"[bold cyan]服务器配额:[/bold cyan] {server_quota}")

    # 设置配置
    os.environ['FT_HOST'] = host
    os.environ['FT_PORT'] = str(port)
    os.environ['FT_STORAGE'] = storage
    os.environ['FT_DATA_DIR'] = data_dir
    os.environ['FT_SERVER_QUOTA'] = server_quota
    os.environ['FT_CLEANUP_INTERVAL'] = str(cleanup_interval)
    os.environ['FT_MAX_SIZE'] = str(max_size)

    # 启动服务器（会自动生成并显示管理员 Token）
    start_server()

# ==================================================
# Token 管理命令
# ==================================================

@app.command("token")
def token_cmd(
    action: str = typer.Argument(..., help="操作: list, create, revoke"),
    label: str = typer.Option(None, "--label", "-l"),
    permissions: str = typer.Option("read,write", "--permissions", "-p"),
    quota: str = typer.Option("10GB", "--quota", "-q")
):
    """管理 API Token"""

    config = _load_config()
    client = FiletransClient(config['server_url'], config['api_token'])

    if action == "list":
        # 列出所有 Token（需要管理员权限）
        result = client.call("admin.manage_token", {
            "action": "list",
            "config": {}
        })
        console.print(result)

    elif action == "create":
        # 创建新 Token
        quota_bytes = _parse_size(quota)
        result = client.call("admin.manage_token", {
            "action": "add",
            "config": {
                "label": label,
                "permissions": permissions.split(","),
                "quota_max_size": quota_bytes
            }
        })
        console.print(f"[bold green]新 Token:[/bold green] {result['token']}")

    elif action == "revoke":
        # 撤销 Token
        token_str = typer.prompt("输入要撤销的 Token")
        result = client.call("admin.manage_token", {
            "action": "revoke",
            "config": {"token": token_str}
        })
        console.print("[bold green]Token 已撤销[/bold green]")

# ==================================================
# 辅助函数
# ==================================================

def _load_config() -> dict:
    """加载配置"""
    if not CONFIG_FILE.exists():
        console.print("[bold red]未找到配置文件，请先运行 'ft init'[/bold red]")
        raise typer.Exit(1)

    import json
    with open(CONFIG_FILE) as f:
        return json.load(f)

def _parse_ttl(ttl: str) -> int:
    """解析 TTL 字符串"""
    import re
    match = re.match(r'(\d+)([smhd])', ttl.lower())
    if not match:
        raise ValueError(f"Invalid TTL format: {ttl}")

    value, unit = match.groups()
    value = int(value)

    multipliers = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400
    }

    return value * multipliers[unit]

def _parse_size(size: str) -> int:
    """解析大小字符串"""
    import re
    match = re.match(r'([\d.]+)([kmgt]?b?)', size.lower())
    if not match:
        raise ValueError(f"Invalid size format: {size}")

    value, unit = match.groups()
    value = float(value)

    multipliers = {
        'b': 1,
        'kb': 1024,
        'mb': 1024**2,
        'gb': 1024**3,
        'tb': 1024**4
    }

    return int(value * multipliers.get(unit, 1))

if __name__ == "__main__":
    app()
```

---

## 8. Web 管理端设计

### 8.1 下载页面 (`/g/<code>`)

```html
<!-- filetrans/web/templates/download.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文件下载 - {{ code }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/axios@1/dist/axios.min.js"></script>
</head>
<body class="bg-gray-900 text-white min-h-screen flex items-center justify-center">
    <div class="max-w-md w-full mx-4">
        <!-- 密码输入框 -->
        <div id="password-section" class="hidden">
            <div class="bg-gray-800 rounded-lg p-8 shadow-xl">
                <h1 class="text-2xl font-bold mb-6 text-center">此文件需要密码</h1>
                <input
                    type="password"
                    id="password-input"
                    class="w-full px-4 py-3 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="请输入下载密码"
                >
                <button
                    onclick="verifyPassword()"
                    class="w-full mt-4 bg-blue-600 hover:bg-blue-700 py-3 rounded-lg font-semibold transition"
                >
                    验证密码
                </button>
                <p id="password-error" class="mt-4 text-red-400 text-center hidden"></p>
            </div>
        </div>

        <!-- 文件信息卡片 -->
        <div id="file-section" class="hidden">
            <div class="bg-gray-800 rounded-lg overflow-hidden shadow-xl">
                <!-- 预览区域 -->
                <div id="preview-container" class="hidden">
                    <img id="image-preview" class="w-full max-h-96 object-contain">
                    <video id="video-preview" class="w-full" controls></video>
                    <pre id="text-preview" class="p-4 text-sm bg-gray-900 overflow-auto max-h-96"></pre>
                </div>

                <!-- 信息区域 -->
                <div class="p-6">
                    <h1 id="filename" class="text-xl font-bold mb-2"></h1>
                    <div class="text-gray-400 text-sm space-y-1">
                        <p>大小: <span id="filesize"></span></p>
                        <p>过期时间: <span id="expires"></span></p>
                        <p>下载次数: <span id="downloads"></span></p>
                    </div>

                    <button
                        onclick="downloadFile()"
                        class="w-full mt-6 bg-blue-600 hover:bg-blue-700 py-3 rounded-lg font-semibold transition flex items-center justify-center"
                    >
                        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
                        </svg>
                        下载文件
                    </button>
                </div>
            </div>
        </div>

        <!-- 加载状态 -->
        <div id="loading" class="text-center">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
            <p class="mt-4 text-gray-400">加载中...</p>
        </div>
    </div>

    <script>
        const CODE = '{{ code }}';
        const API_BASE = '/api/jrpc';
        let downloadUrl = null;

        // 页面加载时获取元数据
        async function init() {
            try {
                const response = await axios.post(API_BASE, {
                    jsonrpc: '2.0',
                    method: 'ft.fetch_metadata',
                    params: { code: CODE },
                    id: 1
                });

                const metadata = response.data.result;

                // 检查是否需要密码
                if (metadata.has_password) {
                    showSection('password-section');
                } else {
                    await verifyPassword(null);
                }

            } catch (error) {
                console.error(error);
                document.getElementById('loading').innerHTML = `
                    <p class="text-red-400">文件不存在或已过期</p>
                `;
            }
        }

        // 验证密码
        async function verifyPassword(password) {
            try {
                const response = await axios.post(API_BASE, {
                    jsonrpc: '2.0',
                    method: 'ft.verify_and_get_link',
                    params: {
                        code: CODE,
                        password: password
                    },
                    id: 1
                });

                const result = response.data.result;

                if (result.need_password) {
                    showSection('password-section');
                    return;
                }

                downloadUrl = result.download_url;
                displayFile(result);

            } catch (error) {
                const errorMsg = error.response?.data?.error?.message || '密码错误';
                document.getElementById('password-error').textContent = errorMsg;
                document.getElementById('password-error').classList.remove('hidden');
            }
        }

        // 显示文件信息
        async function displayFile(data) {
            try {
                // 获取完整元数据
                const metaResponse = await axios.post(API_BASE, {
                    jsonrpc: '2.0',
                    method: 'ft.fetch_metadata',
                    params: { code: CODE },
                    id: 1
                });

                const metadata = metaResponse.data.result;

                document.getElementById('filename').textContent = data.filename || metadata.filename;
                document.getElementById('filesize').textContent = formatSize(metadata.size);
                document.getElementById('expires').textContent = new Date(metadata.expire_at).toLocaleString('zh-CN');
                document.getElementById('downloads').textContent = '不限';

                // 预览处理
                if (metadata.mime_type.startsWith('image/')) {
                    const img = document.getElementById('image-preview');
                    img.src = downloadUrl;
                    document.getElementById('preview-container').classList.remove('hidden');
                } else if (metadata.mime_type.startsWith('video/')) {
                    const video = document.getElementById('video-preview');
                    video.src = downloadUrl;
                    document.getElementById('preview-container').classList.remove('hidden');
                } else if (metadata.mime_type.startsWith('text/')) {
                    const text = document.getElementById('text-preview');
                    const textResponse = await axios.get(downloadUrl);
                    text.textContent = textResponse.data;
                    document.getElementById('preview-container').classList.remove('hidden');
                }

                showSection('file-section');

            } catch (error) {
                console.error(error);
            }
        }

        // 下载文件
        function downloadFile() {
            window.location.href = downloadUrl;
        }

        // 工具函数
        function showSection(id) {
            ['password-section', 'file-section', 'loading'].forEach(sid => {
                document.getElementById(sid).classList.add('hidden');
            });
            document.getElementById(id).classList.remove('hidden');
        }

        function formatSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB';
            return (bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB';
        }

        // 初始化
        init();

        // 回车键提交密码
        document.getElementById('password-input')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const password = document.getElementById('password-input').value;
                verifyPassword(password);
            }
        });
    </script>
</body>
</html>
```

### 8.2 管理后台 (`/admin`)

```html
<!-- filetrans/web/templates/admin.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>filetrans 管理后台</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/axios@1/dist/axios.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="flex h-screen">
        <!-- 侧边栏 -->
        <aside class="w-64 bg-gray-900 text-white">
            <div class="p-6">
                <h1 class="text-2xl font-bold">filetrans</h1>
                <p class="text-gray-400 text-sm">管理后台</p>
            </div>
            <nav class="mt-6">
                <a href="#" onclick="showTab('dashboard')" class="block px-6 py-3 hover:bg-gray-800" id="nav-dashboard">
                    📊 仪表盘
                </a>
                <a href="#" onclick="showTab('files')" class="block px-6 py-3 hover:bg-gray-800" id="nav-files">
                    📁 文件管理
                </a>
                <a href="#" onclick="showTab('tokens')" class="block px-6 py-3 hover:bg-gray-800" id="nav-tokens">
                    🔑 Token 管理
                </a>
                <a href="#" onclick="showTab('settings')" class="block px-6 py-3 hover:bg-gray-800" id="nav-settings">
                    ⚙️ 系统设置
                </a>
            </nav>
        </aside>

        <!-- 主内容 -->
        <main class="flex-1 overflow-auto">
            <!-- 仪表盘 -->
            <div id="tab-dashboard" class="p-8">
                <h2 class="text-3xl font-bold mb-6">仪表盘</h2>

                <!-- 统计卡片 -->
                <div class="grid grid-cols-4 gap-6 mb-8">
                    <div class="bg-white rounded-lg p-6 shadow">
                        <p class="text-gray-500 text-sm">总文件数</p>
                        <p id="stat-total-files" class="text-3xl font-bold">-</p>
                    </div>
                    <div class="bg-white rounded-lg p-6 shadow">
                        <p class="text-gray-500 text-sm">活跃文件</p>
                        <p id="stat-active-files" class="text-3xl font-bold text-green-600">-</p>
                    </div>
                    <div class="bg-white rounded-lg p-6 shadow">
                        <p class="text-gray-500 text-sm">总存储</p>
                        <p id="stat-storage" class="text-3xl font-bold text-blue-600">-</p>
                    </div>
                    <div class="bg-white rounded-lg p-6 shadow">
                        <p class="text-gray-500 text-sm">存储后端</p>
                        <p id="stat-backend" class="text-xl font-bold text-purple-600">-</p>
                    </div>
                </div>

                <!-- 图表 -->
                <div class="bg-white rounded-lg p-6 shadow">
                    <h3 class="text-lg font-semibold mb-4">存储使用趋势</h3>
                    <canvas id="storage-chart"></canvas>
                </div>
            </div>

            <!-- 文件管理 -->
            <div id="tab-files" class="p-8 hidden">
                <div class="flex justify-between items-center mb-6">
                    <h2 class="text-3xl font-bold">文件管理</h2>
                    <button onclick="refreshFiles()" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                        刷新
                    </button>
                </div>

                <div class="bg-white rounded-lg shadow overflow-hidden">
                    <table class="w-full">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">文件名</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">所有者</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">大小</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">过期时间</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
                            </tr>
                        </thead>
                        <tbody id="files-table" class="divide-y divide-gray-200">
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Token 管理 -->
            <div id="tab-tokens" class="p-8 hidden">
                <div class="flex justify-between items-center mb-6">
                    <h2 class="text-3xl font-bold">Token 管理</h2>
                    <button onclick="showCreateTokenModal()" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                        创建 Token
                    </button>
                </div>

                <div class="bg-white rounded-lg shadow overflow-hidden">
                    <table class="w-full">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Token</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">用户</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">标签</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">配额</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
                            </tr>
                        </thead>
                        <tbody id="tokens-table" class="divide-y divide-gray-200">
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- 系统设置 -->
            <div id="tab-settings" class="p-8 hidden">
                <h2 class="text-3xl font-bold mb-6">系统设置</h2>

                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="text-lg font-semibold mb-4">存储配置</h3>
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">存储后端</label>
                            <select id="storage-backend" class="mt-1 block w-full border rounded-lg px-3 py-2">
                                <option value="local">本地存储</option>
                                <option value="s3">AWS S3</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">清理间隔 (秒)</label>
                            <input type="number" id="cleanup-interval" value="60" class="mt-1 block w-full border rounded-lg px-3 py-2">
                        </div>
                    </div>

                    <button onclick="saveSettings()" class="mt-6 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700">
                        保存设置
                    </button>
                </div>
            </div>
        </main>
    </div>

    <script>
        const API_BASE = '/api/jrpc';
        let authToken = localStorage.getItem('ft_admin_token') || prompt('请输入管理员 Token:');

        // jRPC 调用封装
        async function call(method, params = {}) {
            const response = await axios.post(API_BASE, {
                jsonrpc: '2.0',
                method: method,
                params: params,
                id: Date.now()
            }, {
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });
            if (response.data.error) {
                throw new Error(response.data.error.message);
            }
            return response.data.result;
        }

        // 切换 Tab
        function showTab(tab) {
            ['dashboard', 'files', 'tokens', 'settings'].forEach(t => {
                document.getElementById(`tab-${t}`).classList.add('hidden');
                document.getElementById(`nav-${t}`).classList.remove('bg-gray-800');
            });
            document.getElementById(`tab-${tab}`).classList.remove('hidden');
            document.getElementById(`nav-${tab}`).classList.add('bg-gray-800');

            if (tab === 'dashboard') loadDashboard();
            if (tab === 'files') loadFiles();
            if (tab === 'tokens') loadTokens();
        }

        // 加载仪表盘
        async function loadDashboard() {
            const stats = await call('admin.get_stats');
            document.getElementById('stat-total-files').textContent = stats.total_files;
            document.getElementById('stat-active-files').textContent = stats.active_files;
            document.getElementById('stat-storage').textContent = formatSize(stats.total_storage_bytes);
            document.getElementById('stat-backend').textContent = stats.storage_backend;
        }

        // 加载文件列表
        async function loadFiles() {
            const result = await call('admin.list_all');
            const tbody = document.getElementById('files-table');
            tbody.innerHTML = result.files.map(file => `
                <tr>
                    <td class="px-6 py-4 whitespace-nowrap font-mono">${file.code}</td>
                    <td class="px-6 py-4">${file.filename}</td>
                    <td class="px-6 py-4">${file.owner}</td>
                    <td class="px-6 py-4">${formatSize(file.size)}</td>
                    <td class="px-6 py-4">
                        <span class="px-2 py-1 text-xs rounded-full ${getStatusClass(file.status)}">${file.status}</span>
                    </td>
                    <td class="px-6 py-4">${new Date(file.expire_at).toLocaleString('zh-CN')}</td>
                    <td class="px-6 py-4">
                        <button onclick="revokeCode('${file.code}')" class="text-red-600 hover:text-red-800">撤销</button>
                    </td>
                </tr>
            `).join('');
        }

        // 撤销 Code
        async function revokeCode(code) {
            if (confirm(`确定要撤销 ${code} 吗？`)) {
                await call('admin.revoke_code', { code });
                loadFiles();
            }
        }

        // 格式化大小
        function formatSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB';
            return (bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB';
        }

        // 获取状态样式
        function getStatusClass(status) {
            const classes = {
                'active': 'bg-green-100 text-green-800',
                'pending': 'bg-yellow-100 text-yellow-800',
                'expired': 'bg-red-100 text-red-800',
                'revoked': 'bg-gray-100 text-gray-800'
            };
            return classes[status] || 'bg-gray-100 text-gray-800';
        }

        // 初始化
        showTab('dashboard');
    </script>
</body>
</html>
```

---

## 9. 自动化清理机制

### 9.1 Janitor 线程实现

```python
# filetrans/server/janitor.py

import asyncio
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from .database import get_db
from .models import Transfer
from .storage.base import get_storage

class FileJanitor:
    """文件清理服务"""

    def __init__(self, config: dict, storage_backend):
        self.config = config
        self.storage = storage_backend
        self.interval = config.get('janitor', {}).get('interval_seconds', 60)
        self.disk_threshold = config.get('janitor', {}).get('disk_threshold_percent', 10)
        self.running = False

    async def start(self):
        """启动清理任务"""
        self.running = True
        while self.running:
            try:
                await self.cleanup_expired()
                await self.check_disk_space()
            except Exception as e:
                print(f"Janitor error: {e}")

            await asyncio.sleep(self.interval)

    def stop(self):
        """停止清理任务"""
        self.running = False

    async def cleanup_expired(self):
        """清理过期文件"""
        db = next(get_db())

        now = datetime.now()

        # 查找过期或下载次数超限的文件
        expired = db.query(Transfer).filter(
            (Transfer.expire_at < now) |
            ((Transfer.max_downloads != -1) & (Transfer.current_downloads >= Transfer.max_downloads))
        ).all()

        for transfer in expired:
            try:
                # 物理删除文件
                await self.storage.delete_file(transfer.storage_key)

                # 标记状态
                transfer.status = 'expired' if transfer.expire_at < now else 'expired_limit'

                print(f"Cleaned up: {transfer.code}")

            except Exception as e:
                print(f"Failed to cleanup {transfer.code}: {e}")

        db.commit()
        db.close()

    async def check_disk_space(self):
        """检查磁盘空间，必要时强制清理"""
        db = next(get_db())

        # 获取磁盘使用率
        disk_usage = shutil.disk_usage(self.config['storage']['local']['root_dir'])
        used_percent = (disk_usage.used / disk_usage.total) * 100

        if used_percent > (100 - self.disk_threshold):
            print(f"Disk space critical: {used_percent:.1f}% used")

            # 按过期时间排序，优先清理即将过期的
            transfers = db.query(Transfer).filter(
                Transfer.status == 'active'
            ).order_by(Transfer.expire_at.asc()).all()

            freed_bytes = 0
            target_percent = 100 - self.disk_threshold * 2

            for transfer in transfers:
                try:
                    await self.storage.delete_file(transfer.storage_key)
                    transfer.status = 'revoked'
                    freed_bytes += transfer.file_size

                    print(f"Force cleaned: {transfer.code} ({transfer.file_size} bytes)")

                    # 重新检查
                    disk_usage = shutil.disk_usage(self.config['storage']['local']['root_dir'])
                    used_percent = (disk_usage.used / disk_usage.total) * 100

                    if used_percent < target_percent:
                        break

                except Exception as e:
                    print(f"Failed to force cleanup {transfer.code}: {e}")

            db.commit()
            print(f"Freed {freed_bytes} bytes")

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
```

---

## 10. 工程化发布指导

### 10.1 `pyproject.toml` 完整配置

```toml
[project]
name = "filetrans"
version = "1.0.0"
description = "Modern file transfer tool with jRPC API"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [
    { name = "Your Name", email = "your.email@example.com" }
]
keywords = ["file-transfer", "jrpc", "cli", "fastapi"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Communications :: File Sharing",
]

dependencies = [
    # CLI
    "typer[all]>=0.9.0",
    "rich>=13.0.0",
    "requests>=2.28.0",
    "pyclip>=0.7.0",
    "humanize>=4.0.0",

    # Server
    "fastapi>=0.100.0",
    "uvicorn[standard]>=0.23.0",
    "pydantic>=2.0.0",
    "sqlalchemy>=2.0.0",
    "boto3>=1.28.0",

    # Security
    "bcrypt>=4.0.0",
    "cryptography>=41.0.0",

    # Utils
    "python-multipart>=0.0.6",
    "jinja2>=3.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]
s3 = [
    "boto3>=1.28.0",
]

[project.scripts]
ft = "filetrans.cli:app"

[project.urls]
Homepage = "https://github.com/yourusername/filetrans"
Documentation = "https://github.com/yourusername/filetrans#readme"
Repository = "https://github.com/yourusername/filetrans.git"
Issues = "https://github.com/yourusername/filetrans/issues"

[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

# ==================================================
# 工具配置
# ==================================================

[tool.black]
line-length = 100
target-version = ['py310']

[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I", "N"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### 10.2 测试配置

```python
# tests/conftest.py

import pytest
import asyncio
from pathlib import Path

from filetrans.server.main import app
from filetrans.server.database import engine, Base, get_db
from filetrans.server.models import Token, Transfer

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    # 使用内存 SQLite
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()

@pytest.fixture
def test_token(db_session):
    """创建测试 Token"""
    token = Token(
        token="ft_test_token_123456789012345678901234567890",
        user_id="test_user",
        label="Test Token",
        permissions='["read", "write", "admin"]',
        quota_max_size=1073741824,  # 1GB
        is_active=True
    )
    db_session.add(token)
    db_session.commit()
    return token

@pytest.fixture
def client(test_token):
    """FastAPI 测试客户端"""
    from fastapi.testclient import TestClient

    def override_get_db():
        try:
            db = get_db()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        c.headers = {"Authorization": f"Bearer {test_token.token}"}
        yield c

    app.dependency_overrides.clear()
```

### 10.3 本地 S3 模拟 (Docker Compose)

```yaml
# docker-compose.yml
version: '3.8'

services:
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data

  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: filetrans
      POSTGRES_PASSWORD: filetrans
      POSTGRES_DB: filetrans
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  minio_data:
  postgres_data:
```

---

## 11. 增强版功能矩阵

### 11.1 高级功能

| 功能 | 状态 | 说明 |
|------|------|------|
| **空间配额** | ✅ | 限制单 Token 总存储容量和单文件大小 |
| **流量整形** | 🚧 | 限制上传/下载带宽 |
| **分组管理** | ✅ | 文件按命名空间分组 |
| **Webhook 通知** | ✅ | 文件被下载或过期时发送通知 |
| **多版本支持** | 🚧 | 同名文件生成不同 Code |
| **内网穿透** | ❌ | 内置 frp 功能 |

### 11.2 权限系统

```python
# 权限定义
PERMISSIONS = {
    'read': ['ft.fetch_metadata', 'ft.verify_and_get_link', 'ft.list_my_files'],
    'write': ['ft.init_upload', 'ft.confirm_upload'],
    'admin': ['admin.list_all', 'admin.revoke_code', 'admin.manage_token', 'admin.get_stats']
}
```

---

## 12. 下一步开发方向

### 12.1 短期目标 (Phase 1)

- [ ] 实现 CLI 核心命令 (init, push, get, ls)
- [ ] 实现 FastAPI jRPC 服务端
- [ ] 实现 Local 存储后端
- [ ] 实现基础下载页面
- [ ] 实现 Janitor 清理机制

### 12.2 中期目标 (Phase 2)

- [ ] 实现 S3 存储后端
- [ ] 实现管理后台
- [ ] 实现 Token 管理系统
- [ ] 实现 Webhook 通知
- [ ] 添加单元测试

### 12.3 长期目标 (Phase 3)

- [ ] 端到端加密客户端
- [ ] 移动端 App (React Native)
- [ ] 内网穿透集成
- [ ] 多区域部署支持
- [ ] 企业版功能 (SSO、审计日志)

### 12.4 待讨论问题

1. **jRPC 安全性**: 是否需要针对不同 Token 划分独立的存储根目录？
2. **Web 下载体验**: 是否需要支持视频在线点播？
3. **内网穿透**: 是否内置 frp 功能让内网服务器一键暴露到公网？

---

## 附录

### A. 环境变量参考

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `FT_HOST` | 服务绑定地址 | 0.0.0.0 |
| `FT_PORT` | 服务端口 | 8866 |
| `FT_STORAGE` | 存储类型 | local |
| `FT_DATA_DIR` | 数据目录 | ./data |
| `FT_CLEANUP_INTERVAL` | 清理间隔（秒） | 60 |
| `FT_MAX_SIZE` | 单文件最大大小 | 536870912 |
| `FT_S3_BUCKET` | S3 Bucket | - |
| `FT_S3_REGION` | S3 区域 | us-east-1 |
| `FT_S3_ENDPOINT` | S3 端点 | https://s3.amazonaws.com |
| `FT_JWT_SECRET` | JWT 密钥 | - |

### B. 配置文件示例

```bash
# .env.example
FT_HOST=0.0.0.0
FT_PORT=8866
FT_STORAGE=local
FT_DATA_DIR=./data
FT_CLEANUP_INTERVAL=60
FT_MAX_SIZE=536870912

# S3 配置（可选）
FT_S3_BUCKET=filetrans-bucket
FT_S3_REGION=us-east-1
FT_S3_ENDPOINT=https://s3.amazonaws.com
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# 安全配置
FT_JWT_SECRET=change_me_in_production
```

---

**文档版本**: v1.0
**最后更新**: 2024
**维护者**: filetrans 开发团队
