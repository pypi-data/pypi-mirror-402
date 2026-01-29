"""
filetrans jRPC 2.0 API handlers
"""

import random
import string
import bcrypt
from datetime import datetime, timedelta
from fastapi import Header, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from sqlalchemy import or_

from .database import get_db_session
from .models import Transfer, Token, SystemConfig
from .storage.base import get_storage_backend


# ==================================================
# Pydantic 模型定义
# ==================================================

class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: dict = {}
    id: Optional[str | int] = None  # JSON-RPC id can be string or number


class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Optional[dict] = None
    error: Optional[dict] = None
    id: Optional[str | int] = None


class InitUploadParams(BaseModel):
    filename: str
    filesize: int = Field(..., gt=0)
    ttl: int = Field(default=86400, ge=60, le=2592000)
    download_limit: int = Field(default=-1, ge=-1)
    has_password: bool = Field(default=False)
    e2ee: bool = Field(default=False)
    password: Optional[str] = None
    is_public: bool = Field(default=True)
    group: str = Field(default="default")
    file_hash: Optional[str] = None


class VerifyAndGetLinkParams(BaseModel):
    code: str = Field(..., min_length=4, max_length=10)
    password: Optional[str] = None


# ==================================================
# Token 认证依赖
# ==================================================

async def verify_token(authorization: str = Header(...)) -> Token:
    """验证 API Token 并返回 Token 对象"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token_str = authorization[7:]
    db = get_db_session()
    token = db.query(Token).filter(
        Token.token == token_str,
        Token.is_active == True
    ).first()

    if not token:
        raise HTTPException(status_code=401, detail="Invalid or inactive token")

    if token.expires_at and token.expires_at < datetime.now():
        raise HTTPException(status_code=401, detail="Token expired")

    db.close()
    return token


async def get_storage():
    """获取存储后端"""
    from .config import get_config
    config = get_config()
    return get_storage_backend(config)


# ==================================================
# jRPC 方法实现
# ==================================================

async def handle_init_upload(
    params: dict,
    token: Token,
    storage,
    db
) -> dict:
    """初始化上传任务"""
    p = InitUploadParams(**params)

    # 检查用户配额
    if token.quota_current_size + p.filesize > token.quota_max_size:
        raise ValueError(f"User quota exceeded. Available: {token.quota_max_size - token.quota_current_size}")

    if p.filesize > token.max_file_size:
        raise ValueError(f"File size exceeds limit of {token.max_file_size} bytes")

    # 检查服务器配额
    system_config = db.query(SystemConfig).first()
    if system_config.server_current_bytes + p.filesize > system_config.server_quota_bytes:
        raise ValueError(f"Server quota exceeded. Available: {system_config.server_quota_bytes - system_config.server_current_bytes}")

    # 生成唯一 Code
    code = _generate_code()
    while db.query(Transfer).filter(Transfer.code == code).first():
        code = _generate_code()

    # 生成存储 Key 和预签名 URL
    storage_key = storage.generate_storage_key(token.user_id, code, p.filename)
    upload_url, storage_key = await storage.generate_upload_url(
        user_id=token.user_id,
        code=code,
        filename=p.filename,
        ttl_seconds=p.ttl
    )

    # 计算密码哈希
    pwd_hash = None
    if p.has_password and p.password:
        pwd_hash = bcrypt.hashpw(p.password.encode(), bcrypt.gensalt()).decode()

    # 创建数据库记录
    transfer = Transfer(
        code=code,
        owner_id=token.user_id,
        group_name=p.group,
        file_name=p.filename,
        file_size=p.filesize,
        mime_type=_guess_mime_type(p.filename),
        file_hash=p.file_hash,
        storage_mode=storage.config['storage']['backend'].upper(),
        storage_key=storage_key,
        pwd_hash=pwd_hash,
        is_e2ee=p.e2ee,
        is_public=p.is_public,
        status='pending',
        expire_at=datetime.now() + timedelta(seconds=p.ttl),
        max_downloads=p.download_limit
    )
    db.add(transfer)
    db.commit()

    return {
        "code": code,
        "mode": storage.config['storage']['backend'].upper(),
        "upload_url": upload_url,
        "view_url": f"{storage.config['storage']['base_url']}/g/{code}"
    }


async def handle_confirm_upload(params: dict, token: Token, storage, db) -> dict:
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

        # 更新服务器配额
        system_config = db.query(SystemConfig).first()
        if system_config:
            system_config.server_current_bytes += transfer.file_size
    else:
        transfer.status = 'failed'
        await storage.delete_file(transfer.storage_key)

    db.commit()
    return {"success": True}


async def handle_fetch_metadata(params: dict, token: Token, storage, db) -> dict:
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
        "expire_at": transfer.expire_at.isoformat(),
        "is_public": transfer.is_public
    }


async def handle_verify_and_get_link(params: dict, token: Token, storage, db) -> dict:
    """验证密码并获取下载链接"""
    p = VerifyAndGetLinkParams(**params)

    transfer = db.query(Transfer).filter(Transfer.code == p.code).first()

    if not transfer:
        raise ValueError("Transfer not found")

    if transfer.status != 'active':
        raise ValueError(f"Transfer is {transfer.status}")

    if transfer.expire_at < datetime.now():
        transfer.status = 'expired'
        db.commit()
        raise ValueError("Transfer has expired")

    if transfer.max_downloads != -1 and transfer.current_downloads >= transfer.max_downloads:
        raise ValueError("Download limit exceeded")

    if transfer.pwd_hash:
        if not p.password:
            return {"need_password": True}
        if not bcrypt.checkpw(p.password.encode(), transfer.pwd_hash.encode()):
            raise ValueError("Invalid password")

    download_url = await storage.generate_download_url(
        storage_key=transfer.storage_key,
        ttl_seconds=3600
    )

    transfer.current_downloads += 1
    db.commit()

    return {
        "download_url": download_url,
        "filename": transfer.file_name
    }


async def handle_list_my_files(params: dict, token: Token, storage, db) -> dict:
    """列出文件（默认只显示自己的文件）"""
    page = params.get('page', 1)
    page_size = params.get('page_size', 20)
    include_others = params.get('include_others', False)  # 是否包含其他用户的公开文件
    include_expired = params.get('include_expired', True)  # 默认显示过期文件

    if include_others:
        query = db.query(Transfer).filter(
            or_(
                Transfer.owner_id == token.user_id,
                Transfer.is_public == True
            )
        )
    else:
        query = db.query(Transfer).filter(Transfer.owner_id == token.user_id)

    # 只过滤掉已撤销的文件
    query = query.filter(Transfer.status != 'revoked')
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
                "status": t.status,
                "is_expired": t.expire_at < datetime.now()
            }
            for t in transfers
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }


async def handle_download_my_file(params: dict, token: Token, storage, db) -> dict:
    """文件所有者下载自己的文件（即使过期）"""
    code = params['code']

    transfer = db.query(Transfer).filter(Transfer.code == code).first()

    if not transfer:
        raise ValueError("Transfer not found")

    # 检查是否是文件所有者
    if transfer.owner_id != token.user_id:
        raise ValueError("Permission denied: You are not the owner of this file")

    # 检查下载次数限制
    if transfer.max_downloads != -1 and transfer.current_downloads >= transfer.max_downloads:
        raise ValueError("Download limit exceeded")

    # 生成下载链接
    download_url = await storage.generate_download_url(
        storage_key=transfer.storage_key,
        ttl_seconds=3600
    )

    # 如果文件是活跃状态，增加下载计数
    if transfer.status == 'active':
        transfer.current_downloads += 1
        db.commit()

    return {
        "download_url": download_url,
        "filename": transfer.file_name
    }


async def handle_extend_my_file(params: dict, token: Token, storage, db) -> dict:
    """延长自己的文件有效期"""
    code = params['code']
    ttl = params.get('ttl', 86400)  # 默认延长24小时

    transfer = db.query(Transfer).filter(Transfer.code == code).first()

    if not transfer:
        raise ValueError("Transfer not found")

    # 检查是否是文件所有者
    if transfer.owner_id != token.user_id:
        raise ValueError("Permission denied: You are not the owner of this file")

    # 延长有效期
    if transfer.status == 'expired':
        # 如果已过期，从现在开始计算
        transfer.expire_at = datetime.now() + timedelta(seconds=ttl)
        transfer.status = 'active'
    else:
        # 如果未过期，在原有时间上增加
        transfer.expire_at = transfer.expire_at + timedelta(seconds=ttl)

    db.commit()

    return {
        "status": "extended",
        "code": code,
        "new_expire_at": transfer.expire_at.isoformat()
    }


async def handle_delete_my_file(params: dict, token: Token, storage, db) -> dict:
    """删除自己的文件"""
    code = params['code']

    transfer = db.query(Transfer).filter(Transfer.code == code).first()

    if not transfer:
        raise ValueError("Transfer not found")

    # 检查是否是文件所有者
    if transfer.owner_id != token.user_id:
        raise ValueError("Permission denied: You are not the owner of this file")

    # 删除文件
    await storage.delete_file(transfer.storage_key)

    # 更新配额
    system_config = db.query(SystemConfig).first()
    system_config.server_current_bytes -= transfer.file_size

    tkn = db.query(Token).filter(Token.user_id == transfer.owner_id).first()
    if tkn and tkn.quota_current_size >= transfer.file_size:
        tkn.quota_current_size -= transfer.file_size

    # 标记为已撤销
    transfer.status = 'revoked'
    db.commit()

    return {
        "status": "deleted",
        "code": code
    }


# ==================================================
# 管理员方法
# ==================================================

async def handle_admin_list_all(params: dict, token: Token, storage, db) -> dict:
    """管理员：列出所有文件"""
    if not token.is_admin:
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
                "is_public": t.is_public,
                "expire_at": t.expire_at.isoformat()
            }
            for t in transfers
        ]
    }


async def handle_admin_revoke_code(params: dict, token: Token, storage, db) -> dict:
    """管理员：强制撤销 Code"""
    if not token.is_admin:
        raise ValueError("Admin permission required")

    code = params['code']
    transfer = db.query(Transfer).filter(Transfer.code == code).first()

    if not transfer:
        raise ValueError("Transfer not found")

    await storage.delete_file(transfer.storage_key)

    # 更新用户配额
    tkn = db.query(Token).filter(Token.user_id == transfer.owner_id).first()
    if tkn and tkn.quota_current_size >= transfer.file_size:
        tkn.quota_current_size -= transfer.file_size

    # 删除记录
    db.delete(transfer)
    db.commit()

    # 重新计算服务器实际使用量
    from sqlalchemy import func
    total_size = db.query(func.sum(Transfer.file_size)).scalar() or 0
    system_config = db.query(SystemConfig).first()
    system_config.server_current_bytes = total_size
    db.commit()

    return {"status": "revoked"}


async def handle_admin_manage_token(params: dict, token: Token, storage, db) -> dict:
    """管理员：管理 API Token"""
    if not token.is_admin:
        raise ValueError("Admin permission required")

    action = params['action']
    config = params.get('config', {})

    if action == 'add':
        from .config import generate_user_token
        new_token_str = generate_user_token()
        db_token = Token(
            token=new_token_str,
            user_id=config.get('user_id', 'user_' + new_token_str[:8]),
            label=config.get('label', ''),
            permissions=config.get('permissions', 'read,write'),
            quota_max_size=config.get('quota_max_size', 10 * 1024 * 1024 * 1024),
            is_admin=config.get('is_admin', False)
        )
        db.add(db_token)
        db.commit()
        return {"token": new_token_str, "status": "created"}

    elif action == 'revoke':
        # 支持通过 token 或 user_id 撤销
        token_str = config.get('token')
        user_id = config.get('user_id')

        if token_str:
            db_token = db.query(Token).filter(Token.token == token_str).first()
        elif user_id:
            db_token = db.query(Token).filter(Token.user_id == user_id).first()
        else:
            raise ValueError("Must provide either 'token' or 'user_id'")

        if db_token:
            db_token.is_active = False
            db.commit()
        return {"status": "revoked"}

    return {"status": "unknown_action"}


async def handle_admin_list_users(params: dict, token: Token, storage, db) -> dict:
    """管理员：列出所有用户"""
    if not token.is_admin:
        raise ValueError("Admin permission required")

    users = db.query(Token).all()
    return {
        "users": [
            {
                "user_id": u.user_id,
                "label": u.label,
                "quota_max_size": u.quota_max_size,
                "quota_current_size": u.quota_current_size,
                "quota_used_percent": round(u.quota_current_size / u.quota_max_size * 100, 1) if u.quota_max_size > 0 else 0,
                "is_active": u.is_active,
                "is_admin": u.is_admin,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "permissions": u.permissions
            }
            for u in users
        ]
    }


async def handle_admin_get_stats(params: dict, token: Token, storage, db) -> dict:
    """管理员：获取统计信息"""
    if not token.is_admin:
        raise ValueError("Admin permission required")

    from sqlalchemy import func

    total_files = db.query(func.count(Transfer.id)).scalar()
    total_size = db.query(func.sum(Transfer.file_size)).scalar() or 0
    active_files = db.query(func.count(Transfer.id)).filter(Transfer.status == 'active').scalar()
    public_files = db.query(func.count(Transfer.id)).filter(Transfer.is_public == True).scalar()

    system_config = db.query(SystemConfig).first()

    # 如果服务器使用量为负数或与实际不符，重新计算
    if system_config.server_current_bytes < 0 or system_config.server_current_bytes != total_size:
        system_config.server_current_bytes = total_size
        db.commit()

    return {
        "total_files": total_files,
        "active_files": active_files,
        "public_files": public_files,
        "total_storage_bytes": total_size,
        "server_quota_bytes": system_config.server_quota_bytes,
        "server_current_bytes": system_config.server_current_bytes,
        "storage_backend": storage.config['storage']['backend']
    }


async def handle_admin_get_storage_config(params: dict, token: Token, storage, db) -> dict:
    """管理员：获取存储配置"""
    if not token.is_admin:
        raise ValueError("Admin permission required")

    return {
        "backend": storage.config['storage']['backend'],
        "local": storage.config['storage'].get('local', {}),
        "s3": storage.config['storage'].get('s3', {}),
        "base_url": storage.config['storage']['base_url']
    }


async def handle_admin_update_storage_config(params: dict, token: Token, storage, db) -> dict:
    """管理员：更新存储配置（会清空所有文件）"""
    if not token.is_admin:
        raise ValueError("Admin permission required")

    backend = params.get('backend')
    confirm = params.get('confirm', False)

    if not confirm:
        raise ValueError("请确认要清空所有文件（设置 confirm=true）")

    # 获取所有文件并删除
    transfers = db.query(Transfer).all()
    for transfer in transfers:
        try:
            await storage.delete_file(transfer.storage_key)
        except:
            pass

    # 删除所有数据库记录
    db.query(Transfer).delete()
    db.commit()

    # 重置服务器配额
    system_config = db.query(SystemConfig).first()
    system_config.server_current_bytes = 0
    db.commit()

    # 更新配置文件
    import os
    import sys
    from .config import get_config_path

    config_path = get_config_path()
    if config_path.exists():
        import json
        with open(config_path, 'r') as f:
            config = json.load(f)

        # 更新存储配置
        config['storage']['backend'] = backend

        if backend == 'local':
            config['storage']['local'] = params.get('local', {})
        elif backend == 's3':
            config['storage']['s3'] = params.get('s3', {})

        # 写回配置文件
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

    # 触发重启（延迟执行，让响应先返回）
    import threading
    def restart_server():
        import time
        time.sleep(1)  # 等待响应发送
        print("[filetrans] 配置已更新，正在重启服务器...")
        sys.exit(0)  # 退出进程，Docker/进程管理器会自动重启

    thread = threading.Thread(target=restart_server, daemon=True)
    thread.start()

    return {
        "status": "success",
        "message": "存储配置已更新，所有文件已清空，服务器正在重启...",
        "backend": backend,
        "restarting": True
    }


# ==================================================
# 剪贴板方法
# ==================================================

async def handle_clipboard_copy(params: dict, token: Token, storage, db) -> dict:
    """复制内容到剪贴板"""
    from .models import Clipboard

    content_type = params.get('type', 'text')  # 'text' or 'file'
    text_content = params.get('text')
    file_code = params.get('file_code')
    filename = params.get('filename')
    size = params.get('size', 0)

    # 删除该用户旧的剪贴板内容
    db.query(Clipboard).filter(Clipboard.user_id == token.user_id).delete()

    # 创建新的剪贴板记录
    clipboard = Clipboard(
        user_id=token.user_id,
        content_type=content_type,
        text_content=text_content,
        file_code=file_code,
        filename=filename,
        size=size
    )
    db.add(clipboard)
    db.commit()

    return {
        "status": "success",
        "message": "已复制到剪贴板",
        "type": content_type,
        "filename": filename
    }


async def handle_clipboard_paste(params: dict, token: Token, storage, db) -> dict:
    """从剪贴板粘贴内容"""
    from .models import Clipboard
    from .models import Transfer

    # 获取用户的剪贴板内容
    clipboard = db.query(Clipboard).filter(
        Clipboard.user_id == token.user_id
    ).first()

    if not clipboard:
        return {
            "status": "error",
            "message": "剪贴板为空"
        }

    result = {
        "status": "success",
        "type": clipboard.content_type,
        "created_at": clipboard.created_at.isoformat()
    }

    if clipboard.content_type == 'text':
        result.update({
            "text": clipboard.text_content,
            "filename": clipboard.filename
        })
    elif clipboard.content_type == 'file':
        # 获取文件信息
        transfer = db.query(Transfer).filter(
            Transfer.code == clipboard.file_code,
            Transfer.owner_id == token.user_id
        ).first()

        if not transfer:
            return {
                "status": "error",
                "message": "剪贴板中的文件已不存在"
            }

        result.update({
            "code": transfer.code,
            "filename": transfer.file_name,
            "size": transfer.file_size,
            "mime_type": transfer.mime_type,
            "is_e2ee": transfer.is_e2ee,
            "has_password": transfer.pwd_hash is not None
        })

    return result


async def handle_clipboard_clear(params: dict, token: Token, storage, db) -> dict:
    """清空剪贴板"""
    from .models import Clipboard

    deleted = db.query(Clipboard).filter(
        Clipboard.user_id == token.user_id
    ).delete()

    db.commit()

    return {
        "status": "success",
        "message": "剪贴板已清空",
        "deleted_count": deleted
    }


# ==================================================
# 方法映射表
# ==================================================

METHOD_MAP = {
    "ft.init_upload": handle_init_upload,
    "ft.confirm_upload": handle_confirm_upload,
    "ft.fetch_metadata": handle_fetch_metadata,
    "ft.verify_and_get_link": handle_verify_and_get_link,
    "ft.list_my_files": handle_list_my_files,
    "ft.download_my_file": handle_download_my_file,
    "ft.extend_my_file": handle_extend_my_file,
    "ft.delete_my_file": handle_delete_my_file,
    "clipboard.copy": handle_clipboard_copy,
    "clipboard.paste": handle_clipboard_paste,
    "clipboard.clear": handle_clipboard_clear,
    "admin.list_all": handle_admin_list_all,
    "admin.revoke_code": handle_admin_revoke_code,
    "admin.manage_token": handle_admin_manage_token,
    "admin.list_users": handle_admin_list_users,
    "admin.get_stats": handle_admin_get_stats,
    "admin.get_storage_config": handle_admin_get_storage_config,
    "admin.update_storage_config": handle_admin_update_storage_config,
}


async def dispatch_jrpc(
    request: JSONRPCRequest,
    token: Token,
    storage,
    db
) -> JSONRPCResponse:
    """jRPC 请求分发"""
    handler = METHOD_MAP.get(request.method)
    if not handler:
        return JSONRPCResponse(
            id=request.id,
            error={"code": -32601, "message": "Method not found"}
        )

    try:
        result = await handler(request.params, token, storage, db)
        return JSONRPCResponse(id=request.id, result=result)
    except ValueError as e:
        return JSONRPCResponse(
            id=request.id,
            error={"code": -32602, "message": str(e)}
        )
    except Exception as e:
        return JSONRPCResponse(
            id=request.id,
            error={"code": -32603, "message": str(e)}
        )


# ==================================================
# 辅助函数
# ==================================================

def _generate_code(length: int = 6) -> str:
    """生成随机短码"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def _guess_mime_type(filename: str) -> str:
    """简单 MIME 类型检测"""
    import mimetypes
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'
