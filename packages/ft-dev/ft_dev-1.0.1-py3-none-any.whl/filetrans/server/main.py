"""
filetrans FastAPI server
"""

import os
import secrets
import threading
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from .jrpc import JSONRPCRequest, dispatch_jrpc, verify_token, get_storage
from .database import init_db, get_db_session
from .models import Token, SystemConfig
from .config import get_config, generate_admin_token
from .janitor import start_janitor
from .storage.base import get_storage_backend


# 创建 FastAPI 应用
app = FastAPI(
    title="filetrans",
    description="Modern file transfer service with jRPC API",
    version="1.0.0"
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
_storage = None
_config = None
_admin_token_displayed = False


# ==================================================
# 启动事件
# ==================================================

@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    global _storage, _config, _admin_token_displayed

    # 初始化配置
    _config = get_config()

    # 初始化数据库
    init_db()

    # 初始化存储后端
    _storage = get_storage_backend(_config)

    # 创建管理员 Token（如果不存在）
    db = get_db_session()
    admin_token = db.query(Token).filter(Token.is_admin == True).first()

    if not admin_token:
        admin_token_str = generate_admin_token()
        admin_token = Token(
            token=admin_token_str,
            user_id="admin",
            label="Administrator",
            permissions='["read", "write", "admin"]',
            quota_max_size=10 * 1024 * 1024 * 1024 * 1024,  # 10TB
            is_admin=True
        )
        db.add(admin_token)
        db.commit()

        _admin_token = admin_token_str
    else:
        _admin_token = admin_token.token

    db.close()

    # 启动清理任务
    start_janitor(_config, _storage)

    # 延迟显示管理员 Token（让服务器先启动）
    def display_admin_token():
        global _admin_token_displayed
        time.sleep(1)
        print("\n" + "=" * 60)
        print("     ADMIN TOKEN GENERATED (SAVE THIS!)")
        print("=" * 60)
        print(f"  {_admin_token}")
        print("=" * 60)
        print("  Use this token to access admin features.")
        print("  Run 'ft init' and use this token to connect.")
        print("=" * 60 + "\n")
        _admin_token_displayed = True

    if not _admin_token_displayed:
        thread = threading.Thread(target=display_admin_token, daemon=True)
        thread.start()


# ==================================================
# jRPC API
# ==================================================

@app.post("/api/jrpc")
async def jrpc_endpoint(http_request: Request, request: JSONRPCRequest):
    """jRPC 2.0 端点"""
    try:
        # 从请求头获取 Token
        auth_header = http_request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": 401, "message": "Missing authorization header"},
                    "id": request.id
                }
            )

        # 验证 Token
        token = await verify_token(auth_header)

        # 获取存储后端
        storage = _storage or await get_storage()

        # 获取数据库会话
        db = get_db_session()

        # 分发请求
        response = await dispatch_jrpc(request, token, storage, db)

        db.close()
        return response

    except HTTPException as e:
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": e.status_code, "message": e.detail},
                "id": request.id
            }
        )
    except Exception as e:
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": str(e)},
                "id": request.id
            }
        )


# ==================================================
# 公开 API (不需要认证，用于下载页面)
# ==================================================

@app.post("/api/public/jrpc")
async def public_jrpc_endpoint(http_request: Request):
    """公开 jRPC 端点（仅用于获取文件信息和下载链接）"""
    try:
        # 手动解析 JSON
        body = await http_request.body()
        import json
        data = json.loads(body)
        method = data.get("method")
        params = data.get("params", {})
        req_id = data.get("id")

        # 只允许特定方法
        allowed_methods = {"ft.fetch_metadata", "ft.verify_and_get_link"}
        if method not in allowed_methods:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": 403, "message": f"Method not allowed in public endpoint"},
                    "id": req_id
                }
            )

        # 获取存储后端
        storage = _storage or await get_storage()

        # 获取数据库会话
        db = get_db_session()

        # 使用虚拟 Token（无权限限制）
        from .models import Token
        dummy_token = Token(
            user_id="public",
            is_admin=False
        )

        # 创建虚拟请求对象
        from .jrpc import JSONRPCRequest
        jrpc_req = JSONRPCRequest(
            jsonrpc="2.0",
            method=method,
            params=params,
            id=req_id
        )

        # 分发请求
        response = await dispatch_jrpc(jrpc_req, dummy_token, storage, db)

        db.close()
        return response

    except Exception as e:
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": str(e)},
                "id": data.get("id") if 'data' in locals() else None
            }
        )


# ==================================================
# 本地存储上传/下载端点
# ==================================================

@app.get("/api/test")
async def test_endpoint():
    """测试端点"""
    return {"status": "ok", "message": "Server is running"}


@app.put("/api/upload/{storage_key:path}")
async def upload_file_local(storage_key: str, request: Request):
    """本地存储上传端点"""
    if _storage.config['storage']['backend'].upper() != 'LOCAL':
        raise HTTPException(status_code=400, detail="Upload endpoint only available for LOCAL storage")

    from .storage.local import LocalStorage
    storage: LocalStorage = _storage

    file_path = storage.get_full_path(storage_key)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    content = await request.body()

    with open(file_path, 'wb') as f:
        f.write(content)

    return {"status": "ok", "size": len(content)}


@app.get("/api/download/{storage_key:path}")
async def download_file_local(storage_key: str):
    """本地存储下载端点"""
    if _storage.config['storage']['backend'].upper() != 'LOCAL':
        raise HTTPException(status_code=400, detail="Download endpoint only available for LOCAL storage")

    from .storage.local import LocalStorage
    from fastapi.responses import FileResponse
    storage: LocalStorage = _storage

    file_path = storage.get_full_path(storage_key)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)


# ==================================================
# Web 页面
# ==================================================

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


# ==================================================
# 服务器入口
# ==================================================

def serve():
    """启动服务器"""
    config = get_config()

    print("\n" + "=" * 50)
    print("  filetrans - File Transfer Server")
    print("=" * 50)
    print(f"  Host: {config['server']['host']}")
    print(f"  Port: {config['server']['port']}")
    print(f"  Storage: {config['storage']['backend']}")
    print(f"  Data Dir: {config['storage']['local'].get('root_dir', 'N/A')}")
    print("=" * 50 + "\n")

    uvicorn.run(
        "filetrans.server.main:app",
        host=config['server']['host'],
        port=config['server']['port'],
        log_level="info"
    )


if __name__ == "__main__":
    serve()
