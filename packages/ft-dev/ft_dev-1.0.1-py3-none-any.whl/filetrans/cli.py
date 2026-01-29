"""
filetrans CLI - Command Line Interface
"""

import os
import json
import hashlib
import re
import typer
import requests
import humanize
from pathlib import Path
from datetime import datetime
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TimeRemainingColumn
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import Optional

from .client.api import FiletransClient

app = typer.Typer(name="ft", help="filetrans - Modern file transfer tool")
console = Console()

CONFIG_DIR = Path.home() / ".config" / "filetrans"
CONFIG_FILE = CONFIG_DIR / "config.json"


# ==================================================
# 帮助命令
# ==================================================

@app.command()
def help():
    """显示完整的命令参数列表"""
    help_text = """
[bold cyan]命令列表:[/bold cyan]

[bold yellow]ft init[/bold yellow]
  初始化 CLI 配置
  参数: 无（交互式输入）

[bold yellow]ft help[/bold yellow]
  显示完整的命令参数列表

[bold yellow]ft status[/bold yellow]
  查看客户端和服务端状态
  参数: 无

[bold cyan]文件传输命令:[/bold cyan]

[bold yellow]ft push[/bold yellow] / [bold yellow]ft upload[/bold yellow]
  上传文件或文本
  参数:
    PATH                    文件路径或文本内容（用引号包裹）
    --ttl, -t               有效期（如 1h, 30m, 1d）默认: 24h
    --limit, -l             下载次数限制，默认: -1（无限制）
    --pass, -P              下载密码
    --encrypt, -e           端到端加密（仅文件上传）
    --public/--private      是否公开（同服务器内可见），默认: --public
    --copy, -c              复制到剪贴板
    --silent, -s            静默模式

[bold yellow]ft get[/bold yellow] / [bold yellow]ft download[/bold yellow]
  下载文件
  参数:
    CODE                    提取码
    --output, -o            输出路径
    --pass, -P              下载密码
    --decrypt-key, -d       E2EE 解密密钥

[bold yellow]ft ls[/bold yellow]
  列出我的文件
  参数:
    --page, -p              页码，默认: 1
    --size, -s              每页数量，默认: 20
    --expired, -e           是否包含过期文件，默认: 是
    --others, -o            显示其他用户的公开文件

[bold yellow]ft extend[/bold yellow]
  延长自己的文件有效期
  参数:
    CODE                    文件 Code
    --ttl, -t               延长时间（如 1h, 7d），默认: 24h

[bold yellow]ft delete[/bold yellow]
  删除自己的文件
  参数:
    CODE                    文件 Code

[bold cyan]剪贴板命令:[/bold cyan]

[bold yellow]ft c[/bold yellow]
  上传本地剪贴板内容到服务器（支持文本和图片）
  参数: 无（自动读取系统剪贴板）

[bold yellow]ft v[/bold yellow]
  从服务器拉取剪贴板内容到本地
  参数: 无（自动复制到系统剪贴板）

[bold yellow]ft clear[/bold yellow]
  清空云端剪贴板
  参数: 无

[bold cyan]管理命令:[/bold cyan]

[bold yellow]ft config[/bold yellow]
  管理存储配置（需要管理员权限）
  参数:
    ACTION                  操作: show, set
    --backend, -b           存储后端 (local/s3)
    --local-dir             本地存储目录
    --s3-bucket             S3 Bucket 名称
    --s3-region             S3 Region
    --s3-endpoint           S3 Endpoint URL
    --confirm, -y           确认清空所有文件

[bold yellow]ft serve[/bold yellow]
  启动服务器（自动生成管理员 Token）
  参数:
    --host, -h              主机地址，默认: 0.0.0.0
    --port, -p              端口，默认: 8866
    --storage, -s           存储类型 (local/s3)，默认: local
    --data-dir, -d          数据目录，默认: ./data
    --server-quota, -q      服务器总配额，默认: 100GB
    --cleanup-interval      清理间隔（秒），默认: 60
    --max-size              单文件最大大小，默认: 536870912

[bold yellow]ft token[/bold yellow]
  管理 API Token（需要管理员权限）
  参数:
    ACTION                  操作: list, create, revoke
    --user-id, -u           用户 ID（用于 revoke）
    --label, -l             标签
    --permissions, -p       权限，默认: read,write
    --quota, -q             配额，默认: 10GB

[bold cyan]示例:[/bold cyan]

[bold yellow]文件传输:[/bold yellow]
  ft push myfile.txt --ttl 1h              上传文件，1小时有效期
  ft push "这是文本内容"                    上传文本
  ft push ~/Documents/project.zip --private 上传私有文件
  ft get ABC123                             下载文件
  ft get ABC123 -o ~/Downloads/             下载到指定目录
  ft ls                                     列出我的文件
  ft ls -o                                  列出我的文件和其他公开文件
  ft extend ABC123 --ttl 7d                 延长文件有效期 7 天
  ft delete ABC123                          删除文件

[bold yellow]剪贴板:[/bold yellow]
  ft c                                      复制本地剪贴板到服务器
  ft v                                      从服务器粘贴到本地剪贴板
  ft clear                                  清空云端剪贴板

[bold yellow]管理:[/bold yellow]
  ft status                                 查看状态
  ft config show                            查看存储配置
  ft config set -b local --local-dir ./data -y
  ft config set -b s3 --s3-bucket mybucket -y
  ft serve --port 8080                      启动服务器
  ft token list                             列出所有用户
  ft token create --label "我的设备" --quota 50GB
  ft token revoke -u user123                撤销用户 Token

[bold yellow]有效期格式:[/bold yellow]
  1h, 2h, 12h                               小时
  1d, 7d, 30d                               天
  1w, 4w                                    周

[bold yellow]配额格式:[/bold yellow]
  100MB, 1GB, 10GB, 1TB                     大小
"""
    console.print(help_text)


# ==================================================
# 初始化命令
# ==================================================

@app.command()
def init():
    """初始化 CLI 配置"""

    console.print(Panel("[bold blue]filetrans CLI 初始化向导[/bold blue]", padding=(0, 1)))

    server_url = typer.prompt("服务器 URL", default="http://localhost:8866")
    api_token = typer.prompt("API Token", hide_input=True)

    # 验证 Token（使用普通用户接口）
    with console.status("[bold yellow]验证 Token...", spinner="dots"):
        client = FiletransClient(server_url, api_token)
        try:
            # 调用普通用户接口来验证 token 有效性
            result = client.call("ft.list_my_files", {"page": 1, "page_size": 1})
            console.print("[bold green]✓[/bold green] Token 验证成功")
        except Exception as e:
            console.print(f"[bold red]✗[/bold red] Token 验证失败: {e}")
            raise typer.Exit(1)

    # 创建配置目录
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # 写入配置
    config = {
        "server_url": server_url,
        "api_token": api_token
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

    # 设置权限
    os.chmod(CONFIG_FILE, 0o600)

    console.print(f"\n[bold green]✓ 配置已保存到:[/bold green] {CONFIG_FILE}")


# ==================================================
# 状态命令
# ==================================================

@app.command("status")
def status():
    """查看客户端和服务端状态"""

    # 客户端配置状态
    console.print("\n[bold cyan]客户端状态[/bold cyan]")

    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            config = json.load(f)

        console.print(f"  配置文件: [green]{CONFIG_FILE}[/green]")
        console.print(f"  服务器地址: [cyan]{config['server_url']}[/cyan]")
        console.print(f"  Token: [dim]{config['api_token'][:20]}...[/dim]")
    else:
        console.print(f"  配置文件: [red]未配置[/red]")
        console.print(f"  请运行 'ft init' 进行初始化")
        return

    # 服务端状态
    console.print("\n[bold cyan]服务端状态[/bold cyan]")

    client = FiletransClient(config['server_url'], config['api_token'])

    try:
        # 测试连接
        with console.status("[bold yellow]连接服务器...", spinner="dots"):
            # 尝试获取用户文件列表来测试连接
            files_result = client.call("ft.list_my_files", {"page": 1, "page_size": 1})
    except Exception as e:
        console.print(f"  连接状态: [red]失败[/red]")
        console.print(f"  错误信息: {e}")
        return

    console.print(f"  连接状态: [green]在线[/green]")

    # 获取更详细的服务端信息
    try:
        with console.status("[bold yellow]获取服务器信息...", spinner="dots"):
            files_result = client.call("ft.list_my_files", {"page": 1, "page_size": 1})

            # 计算用户统计
            my_files = client.call("ft.list_my_files", {"page": 1, "page_size": 1, "include_public": False})
            total_count = my_files.get('total', 0)

        console.print(f"  我的文件数: [cyan]{total_count}[/cyan]")

        # 如果是管理员，显示服务器统计
        try:
            with console.status("[bold yellow]获取管理员信息...", spinner="dots"):
                stats = client.call("admin.get_stats", {})

            console.print(f"  权限: [yellow]管理员[/yellow]")
            console.print(f"\n  [bold]服务器统计:[/bold]")
            console.print(f"    总文件数: {stats['total_files']}")
            console.print(f"    活跃文件: {stats['active_files']}")
            console.print(f"    总存储: [cyan]{humanize.naturalsize(stats['total_storage_bytes'])}[/cyan]")
            console.print(f"    存储后端: [cyan]{stats['storage_backend']}[/cyan]")
            console.print(f"    服务器配额: {humanize.naturalsize(stats['server_current_bytes'])} / {humanize.naturalsize(stats['server_quota_bytes'])}")
        except:
            console.print(f"  权限: [dim]普通用户[/dim]")

    except Exception as e:
        console.print(f"  获取详细信息: [yellow]部分功能不可用[/yellow]")

    console.print()  # 空行


# ==================================================
# 上传命令
# ==================================================

def _is_text_input(text: str) -> tuple[bool, str]:
    """检测输入是否是文本（引号包裹）"""
    text = text.strip()

    # 检查是否被引号包裹
    if (text.startswith('"') and text.endswith('"')) or \
       (text.startswith("'") and text.endswith("'")) or \
       (text.startswith("`") and text.endswith("`")):
        # 移除引号
        content = text[1:-1]
        return True, content

    return False, None


def _is_text_or_file(text: str) -> tuple[bool, str]:
    """智能判断输入是文本内容还是文件路径"""
    text = text.strip()

    # 1. 检查是否被引号包裹（明确的文本）
    if (text.startswith('"') and text.endswith('"')) or \
       (text.startswith("'") and text.endswith("'")) or \
       (text.startswith("`") and text.endswith("`")):
        # 移除引号
        content = text[1:-1]
        return True, content

    # 2. 检查是否是已存在的文件
    file_path = Path(text)
    if file_path.exists():
        return False, text

    # 3. 既不是被引号包裹，也不是已存在的文件，当作文本处理
    return True, text


def _push_text(
    text: str,
    ttl: str = "24h",
    limit: int = -1,
    password: str = None,
    public: bool = True,
    copy: bool = False,
    silent: bool = False
):
    """上传文本的实现"""
    config = _load_config()
    client = FiletransClient(config['server_url'], config['api_token'])

    ttl_seconds = _parse_ttl(ttl)

    # 文本大小限制（1MB）
    max_text_size = 1024 * 1024  # 1MB
    if len(text.encode('utf-8')) > max_text_size:
        console.print(f"[bold red]✗[/bold red] 文本过大，最大支持 {humanize.naturalsize(max_text_size)}")
        raise typer.Exit(1)

    # 生成文件名
    import time
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"paste_{timestamp}.txt"

    if not silent:
        console.print(f"[bold cyan]上传文本:[/bold cyan] {filename}")
        console.print(f"[bold cyan]大小:[/bold cyan] {humanize.naturalsize(len(text.encode('utf-8')))}")

    # 转换为字节
    file_data = text.encode('utf-8')
    file_hash = hashlib.sha256(file_data).hexdigest()

    # 初始化上传
    result = client.call("ft.init_upload", {
        "filename": filename,
        "filesize": len(file_data),
        "ttl": ttl_seconds,
        "download_limit": limit,
        "has_password": password is not None,
        "password": password,
        "e2ee": False,
        "is_public": public,
        "file_hash": file_hash
    })

    code = result['code']
    upload_url = result['upload_url']
    view_url = result['view_url']

    # 上传文本
    response = requests.put(upload_url, data=file_data)

    if response.status_code not in [200, 201]:
        console.print(f"[bold red]✗ 上传失败:[/bold red] {response.status_code}")
        raise typer.Exit(1)

    # 确认上传
    client.call("ft.confirm_upload", {
        "code": code,
        "status": "success"
    })

    # 输出结果
    if not silent:
        console.print(Panel.fit(
            f"[bold green]✓ 上传成功![/bold green]\n\n"
            f"[bold cyan]Code:[/bold cyan] {code}\n"
            f"[bold cyan]链接:[/bold cyan] {view_url}",
            border_style="green"
        ))
    else:
        console.print(code)

    # 复制到剪贴板
    if copy:
        try:
            import pyclip
            pyclip.copy(view_url)
            console.print("[bold green]✓ 已复制链接到剪贴板[/bold green]")
        except ImportError:
            console.print("[yellow]提示: 安装 pyclip 以启用剪贴板功能[/yellow]")


def _push_impl(
    path: str,
    ttl: str = "24h",
    limit: int = -1,
    password: str = None,
    encrypt: bool = False,
    public: bool = True,
    copy: bool = False,
    silent: bool = False
):
    """上传文件的实现"""
    # 加载配置
    config = _load_config()
    client = FiletransClient(config['server_url'], config['api_token'])

    # 解析 TTL
    ttl_seconds = _parse_ttl(ttl)

    # 读取文件
    file_path = Path(path)
    if not file_path.exists():
        console.print(f"[bold red]✗[/bold red] 文件不存在: {path}")
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
        console.print(Panel(
            f"[bold yellow]请妥善保管以下解密密钥:[/bold yellow]\n[bold red]{key.decode()}[/bold red]",
            title="端到端加密",
            border_style="yellow"
        ))

    # 计算 SHA-256
    file_hash = hashlib.sha256(file_data).hexdigest()

    # 初始化上传
    result = client.call("ft.init_upload", {
        "filename": filename,
        "filesize": len(file_data),
        "ttl": ttl_seconds,
        "download_limit": limit,
        "has_password": password is not None,
        "password": password,
        "e2ee": encrypt,
        "is_public": public,
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
        console.print(f"[bold red]✗ 上传失败:[/bold red] {response.status_code}")
        raise typer.Exit(1)

    # 确认上传
    client.call("ft.confirm_upload", {
        "code": code,
        "status": "success"
    })

    # 输出结果
    if not silent:
        console.print(Panel.fit(
            f"[bold green]✓ 上传成功![/bold green]\n\n"
            f"[bold cyan]Code:[/bold cyan] {code}\n"
            f"[bold cyan]链接:[/bold cyan] {view_url}",
            border_style="green"
        ))
    else:
        console.print(code)

    # 复制到剪贴板
    if copy:
        try:
            import pyclip
            pyclip.copy(view_url)
            console.print("[bold green]✓ 已复制链接到剪贴板[/bold green]")
        except ImportError:
            console.print("[yellow]提示: 安装 pyclip 以启用剪贴板功能[/yellow]")


@app.command("push")
def push(
    path: str = typer.Argument(..., help="文件路径或文本内容（用引号包裹）"),
    ttl: str = typer.Option("24h", "--ttl", "-t", help="有效期（如 1h, 30m, 1d）"),
    limit: int = typer.Option(-1, "--limit", "-l", help="下载次数限制"),
    password: str = typer.Option(None, "--pass", "-P", help="下载密码"),
    encrypt: bool = typer.Option(False, "--encrypt", "-e", help="端到端加密（文件上传）"),
    public: bool = typer.Option(True, "--public/--private", help="是否公开（同服务器内可见）"),
    copy: bool = typer.Option(False, "--copy", "-c", help="复制到剪贴板"),
    silent: bool = typer.Option(False, "--silent", "-s", help="静默模式")
):
    """上传文件或文本（用引号包裹文本内容）"""
    # 智能检测是否为文本输入
    is_text, text_content = _is_text_or_file(path)
    if is_text:
        # 如果是文本，加密选项不适用
        if encrypt:
            console.print("[yellow]注意: 文本上传不支持端到端加密，已忽略 --encrypt 选项[/yellow]")
        _push_text(text_content, ttl, limit, password, public, copy, silent)
    else:
        _push_impl(path, ttl, limit, password, encrypt, public, copy, silent)


@app.command("upload")
def upload(
    path: str = typer.Argument(..., help="文件路径或文本内容（用引号包裹）"),
    ttl: str = typer.Option("24h", "--ttl", "-t", help="有效期（如 1h, 30m, 1d）"),
    limit: int = typer.Option(-1, "--limit", "-l", help="下载次数限制"),
    password: str = typer.Option(None, "--pass", "-P", help="下载密码"),
    encrypt: bool = typer.Option(False, "--encrypt", "-e", help="端到端加密（文件上传）"),
    public: bool = typer.Option(True, "--public/--private", help="是否公开（同服务器内可见）"),
    copy: bool = typer.Option(False, "--copy", "-c", help="复制到剪贴板"),
    silent: bool = typer.Option(False, "--silent", "-s", help="静默模式")
):
    """上传文件或文本（别名）（用引号包裹文本内容）"""
    # 智能检测是否为文本输入
    is_text, text_content = _is_text_or_file(path)
    if is_text:
        # 如果是文本，加密选项不适用
        if encrypt:
            console.print("[yellow]注意: 文本上传不支持端到端加密，已忽略 --encrypt 选项[/yellow]")
        _push_text(text_content, ttl, limit, password, public, copy, silent)
    else:
        _push_impl(path, ttl, limit, password, encrypt, public, copy, silent)


# ==================================================
# 下载命令
# ==================================================

def _get_impl(code: str, output: str = None, password: str = None, decrypt_key: str = None):
    """下载文件的实现"""
    config = _load_config()
    client = FiletransClient(config['server_url'], config['api_token'])

    try:
        # 获取元数据
        try:
            metadata = client.call("ft.fetch_metadata", {"code": code})
        except Exception as e:
            error_msg = str(e)
            if "not found" in error_msg.lower():
                console.print(f"[bold red]✗ 文件不存在:[/bold red] Code {code} 不存在")
            elif "expired" in error_msg.lower() or "expire" in error_msg.lower():
                console.print(f"[bold red]✗ 文件已过期:[/bold red] Code {code} 已过期")
            else:
                console.print(f"[bold red]✗ 获取文件信息失败:[/bold red] {error_msg}")
            raise typer.Exit(1)

        console.print(f"[bold cyan]文件:[/bold cyan] {metadata['filename']}")
        console.print(f"[bold cyan]大小:[/bold cyan] {humanize.naturalsize(metadata['size'])}")

        # 显示文件状态
        if metadata.get('status') == 'expired':
            console.print(f"[bold yellow]⚠ 文件已过期，但所有者仍可下载[/bold yellow]")

        # 获取下载链接
        try:
            result = client.call("ft.verify_and_get_link", {
                "code": code,
                "password": password
            })
        except Exception as e:
            error_msg = str(e)
            if "Invalid password" in error_msg or "password" in error_msg.lower():
                console.print(f"[bold red]✗ 密码错误[/bold red]")
                console.print(f"[bold yellow]提示: 请检查下载密码是否正确[/bold yellow]")
                raise typer.Exit(1)
            elif "not found" in error_msg.lower():
                console.print(f"[bold red]✗ 文件不存在或已过期[/bold red]")
                raise typer.Exit(1)
            elif "expired" in error_msg.lower():
                console.print(f"[bold red]✗ 文件已过期[/bold red]")
                raise typer.Exit(1)
            elif "Download limit exceeded" in error_msg or "limit" in error_msg.lower():
                console.print(f"[bold red]✗ 下载次数已达上限[/bold red]")
                raise typer.Exit(1)
            else:
                console.print(f"[bold red]✗ 验证失败:[/bold red] {error_msg}")
                raise typer.Exit(1)

        if result.get("need_password"):
            max_attempts = 3
            for attempt in range(max_attempts):
                password = typer.prompt("请输入密码", hide_input=True)
                try:
                    result = client.call("ft.verify_and_get_link", {
                        "code": code,
                        "password": password
                    })
                    break
                except Exception as e:
                    error_msg = str(e)
                    if "password" in error_msg.lower() or "Invalid" in error_msg:
                        remaining = max_attempts - attempt - 1
                        if remaining > 0:
                            console.print(f"[bold red]✗ 密码错误，还剩 {remaining} 次机会[/bold red]")
                        else:
                            console.print(f"[bold red]✗ 密码错误次数过多[/bold red]")
                            raise typer.Exit(1)
                    else:
                        raise

        download_url = result['download_url']
        filename = result['filename']

        # 下载文件
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]下载中...", total=metadata['size'])

                response = requests.get(download_url, stream=True, timeout=30)
                response.raise_for_status()

                file_data = b""
                for chunk in response.iter_content(chunk_size=8192):
                    file_data += chunk
                    progress.update(task, advance=len(chunk))
        except requests.exceptions.Timeout:
            console.print(f"[bold red]✗ 下载超时[/bold red]")
            console.print(f"[bold yellow]提示: 请检查网络连接或稍后重试[/bold yellow]")
            raise typer.Exit(1)
        except requests.exceptions.ConnectionError:
            console.print(f"[bold red]✗ 网络连接失败[/bold red]")
            console.print(f"[bold yellow]提示: 请检查服务器地址和网络连接[/bold yellow]")
            raise typer.Exit(1)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                console.print(f"[bold red]✗ 文件不存在[/bold red]")
            elif e.response.status_code == 403:
                console.print(f"[bold red]✗ 无权限访问此文件[/bold red]")
            else:
                console.print(f"[bold red]✗ 下载失败 (HTTP {e.response.status_code})[/bold red]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[bold red]✗ 下载失败:[/bold red] {e}")
            raise typer.Exit(1)

        # E2EE 解密
        if decrypt_key:
            try:
                from cryptography.fernet import Fernet
                cipher = Fernet(decrypt_key.encode())
                file_data = cipher.decrypt(file_data)
            except Exception as e:
                console.print(f"[bold red]✗ 解密失败[/bold red]")
                console.print(f"[bold yellow]提示: 请检查解密密钥是否正确[/bold yellow]")
                raise typer.Exit(1)

        # 输出
        output_path = Path(output) if output else Path.cwd() / filename

        try:
            with open(output_path, "wb") as f:
                f.write(file_data)
        except Exception as e:
            console.print(f"[bold red]✗ 保存文件失败:[/bold red] {e}")
            raise typer.Exit(1)

        console.print(f"\n[bold green]✓ 已保存到:[/bold green] {output_path}")

    except typer.Exit:
        raise
    except KeyboardInterrupt:
        console.print(f"\n[bold yellow]⚠ 操作已取消[/bold yellow]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"[bold red]✗ 发生未预期的错误:[/bold red] {e}")
        raise typer.Exit(1)


@app.command("get")
def get(
    code: str = typer.Argument(..., help="提取码"),
    output: str = typer.Option(None, "--output", "-o", help="输出路径"),
    password: str = typer.Option(None, "--pass", "-P", help="下载密码"),
    decrypt_key: str = typer.Option(None, "--decrypt-key", "-d", help="E2EE 解密密钥")
):
    """下载文件"""
    _get_impl(code, output, password, decrypt_key)


@app.command("download")
def download(
    code: str = typer.Argument(..., help="提取码"),
    output: str = typer.Option(None, "--output", "-o", help="输出路径"),
    password: str = typer.Option(None, "--pass", "-P", help="下载密码"),
    decrypt_key: str = typer.Option(None, "--decrypt-key", "-d", help="E2EE 解密密钥")
):
    """下载文件（别名）"""
    _get_impl(code, output, password, decrypt_key)


# ==================================================
# 列表命令
# ==================================================

@app.command("ls")
def list_files(
    page: int = typer.Option(1, "--page", "-p", help="页码"),
    page_size: int = typer.Option(20, "--size", "-s", help="每页数量"),
    include_expired: bool = typer.Option(True, "--expired", "-e", help="是否包含过期文件"),
    include_others: bool = typer.Option(False, "--others", "-o", help="显示其他用户的公开文件")
):
    """列出我的文件"""

    config = _load_config()
    client = FiletransClient(config['server_url'], config['api_token'])

    result = client.call("ft.list_my_files", {
        "page": page,
        "page_size": page_size,
        "include_expired": include_expired,
        "include_others": include_others
    })

    table = Table(title=f"文件列表 - {'(我的 + 公开)' if include_others else '(我的文件)'}")
    table.add_column("Code", style="cyan")
    table.add_column("文件名", style="white")
    table.add_column("所有者", style="magenta")
    table.add_column("可见性", style="bright_cyan")
    table.add_column("大小", style="green")
    table.add_column("过期时间", style="red")
    table.add_column("状态", style="yellow")

    for file in result['files']:
        owner_display = "[green]你[/green]" if file['is_mine'] else file['owner'][:8] + "..."
        visibility = "[cyan]公开[/cyan]" if file['is_public'] else "[yellow]私有[/yellow]"

        table.add_row(
            file['code'],
            file['filename'][:25] + "..." if len(file['filename']) > 25 else file['filename'],
            owner_display,
            visibility,
            humanize.naturalsize(file['size']),
            file['expire_at'][:10],
            file['status']
        )

    console.print(table)
    console.print(f"\n第 {page} 页，共 {result['total']} 个文件")


# ==================================================
# 文件管理命令
# ==================================================

@app.command("extend")
def extend_file(
    code: str = typer.Argument(..., help="文件 Code"),
    ttl: str = typer.Option("24h", "--ttl", "-t", help="延长时间（如 1h, 7d）")
):
    """延长文件有效期"""
    config = _load_config()
    client = FiletransClient(config['server_url'], config['api_token'])

    ttl_seconds = _parse_ttl(ttl)

    try:
        result = client.call("ft.extend_my_file", {
            "code": code,
            "ttl": ttl_seconds
        })

        new_expire = datetime.fromisoformat(result['new_expire_at']).strftime("%Y-%m-%d %H:%M:%S")
        console.print(f"[bold green]✓ 文件 {code} 已延长[/bold green]")
        console.print(f"  新过期时间: [cyan]{new_expire}[/cyan]")
    except Exception as e:
        console.print(f"[bold red]✗ 延长失败:[/bold red] {e}")
        raise typer.Exit(1)


@app.command("delete")
def delete_file(
    code: str = typer.Argument(..., help="文件 Code")
):
    """删除自己的文件"""
    config = _load_config()
    client = FiletransClient(config['server_url'], config['api_token'])

    if not typer.confirm(f"确定要删除文件 {code} 吗？"):
        raise typer.Exit()

    try:
        result = client.call("ft.delete_my_file", {"code": code})
        console.print(f"[bold green]✓ 文件 {code} 已删除[/bold green]")
    except Exception as e:
        console.print(f"[bold red]✗ 删除失败:[/bold red] {e}")
        raise typer.Exit(1)


# ==================================================
# 剪贴板命令
# ==================================================

def _get_system_clipboard() -> tuple[str, bytes | None]:
    """
    获取系统剪贴板内容
    返回: (type, content)
    type: 'text' 或 'image'
    content: 文本字符串 或 图片字节
    """
    import platform
    import subprocess
    import tempfile

    system = platform.system()

    # 首先尝试获取文本
    if system == "Darwin":  # macOS
        # 使用 pbpaste 获取文本
        try:
            result = subprocess.run(['pbpaste'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout and len(result.stdout.strip()) > 0:
                return 'text', result.stdout.strip()
        except FileNotFoundError:
            pass

        # 尝试使用 pyclip 作为备选
        try:
            import pyclip
            text = pyclip.paste()
            if text and len(text.strip()) > 0:
                return 'text', text.strip()
        except ImportError:
            pass

        # 尝试获取图片
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name

        try:
            # 使用 osascript 获取剪贴板图片
            script = f'''
            tell application "System Events"
                try
                    set theData to the clipboard as «class PNGf»
                    set theFile to open for access POSIX file "{temp_path}" with write permission
                    try
                        write theData to theFile
                    end try
                    close access theFile
                on error
                    return "error"
                end try
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)

            # 如果成功且文件有内容
            if result.returncode == 0 and Path(temp_path).stat().st_size > 100:  # 至少有 100 字节
                with open(temp_path, 'rb') as f:
                    return 'image', f.read()
        finally:
            import os
            if Path(temp_path).exists():
                try:
                    os.unlink(temp_path)
                except:
                    pass

    elif system == "Linux":
        # 尝试获取文本
        try:
            result = subprocess.run(['xclip', '-selection', 'clipboard', '-o'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout and len(result.stdout.strip()) > 0:
                return 'text', result.stdout.strip()
        except FileNotFoundError:
            pass

        # 尝试获取图片
        try:
            result = subprocess.run(
                ['xclip', '-selection', 'clipboard', '-t', 'image/png', '-o'],
                capture_output=True
            )
            if result.returncode == 0 and result.stdout:
                return 'image', result.stdout
        except FileNotFoundError:
            pass

    elif system == "Windows":
        # 尝试获取文本
        try:
            import win32clipboard
            win32clipboard.OpenClipboard()
            try:
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                    text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                    if text and len(text.strip()) > 0:
                        return 'text', text.strip()
            finally:
                win32clipboard.CloseClipboard()
        except ImportError:
            pass
        except Exception:
            pass

        # 尝试获取图片
        try:
            import win32clipboard
            from PIL import Image
            import io

            win32clipboard.OpenClipboard()
            try:
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
                    data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
                    # 将 BMP 转换为 PNG
                    img = Image.open(io.BytesIO(data))
                    output = io.BytesIO()
                    img.save(output, format='PNG')
                    return 'image', output.getvalue()
            finally:
                win32clipboard.CloseClipboard()
        except ImportError:
            pass
        except Exception:
            pass

    # 如果没有获取到内容，返回空
    return 'text', None


def _set_system_clipboard(content_type: str, content: str | bytes):
    """
    设置系统剪贴板内容
    content_type: 'text' 或 'image'
    content: 文本字符串 或 图片字节
    """
    import platform
    import subprocess
    import tempfile

    system = platform.system()

    if content_type == 'text':
        if system == "Darwin":  # macOS
            # 使用 pbcopy
            process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
            process.communicate(content.encode('utf-8'))
        elif system == "Linux":
            try:
                subprocess.run(['xclip', '-selection', 'clipboard'], input=content.encode('utf-8'))
            except FileNotFoundError:
                pass
        elif system == "Windows":
            try:
                import win32clipboard
                win32clipboard.OpenClipboard()
                try:
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, content)
                finally:
                    win32clipboard.CloseClipboard()
            except ImportError:
                pass
            except Exception:
                pass
        else:
            # 其他系统尝试使用 pyclip
            try:
                import pyclip
                pyclip.copy(content)
            except ImportError:
                pass

    elif content_type == 'image':
        if system == "Darwin":  # macOS
            # 将图片保存到临时文件并复制
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                f.write(content)
                temp_path = f.name

            try:
                subprocess.run(
                    ['osascript', '-e', f'set the clipboard to (read file "{temp_path}" as «class PNGf»)'],
                    capture_output=True
                )
            finally:
                import os
                os.unlink(temp_path)

        elif system == "Linux":
            try:
                subprocess.run(
                    ['xclip', '-selection', 'clipboard', '-t', 'image/png'],
                    input=content
                )
            except FileNotFoundError:
                pass

        elif system == "Windows":
            try:
                import win32clipboard
                from PIL import Image
                import io

                # 将 PNG 转换为 BMP
                img = Image.open(io.BytesIO(content))
                output = io.BytesIO()
                img.save(output, format='BMP')
                bmp_data = output.getvalue()

                win32clipboard.OpenClipboard()
                try:
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, bmp_data)
                finally:
                    win32clipboard.CloseClipboard()
            except ImportError:
                pass
            except Exception:
                pass


@app.command("c")
def copy_to_clipboard():
    """读取本地剪贴板（文本或图片），上传到服务器"""
    config = _load_config()
    client = FiletransClient(config['server_url'], config['api_token'])

    content_type, content = _get_system_clipboard()

    if content is None:
        console.print("[bold yellow]剪贴板为空或不支持的内容类型[/bold yellow]")
        raise typer.Exit(0)

    try:
        if content_type == 'text':
            # 上传文本
            text = content
            result = client.call("clipboard.copy", {
                "type": "text",
                "text": text,
                "filename": f"文本 ({len(text)} 字符)",
                "size": len(text.encode('utf-8'))
            })
            console.print(f"[bold green]✓ 上传成功[/bold green]")
            console.print(f"  类型: 文本")
            console.print(f"  内容: {text[:50]}{'...' if len(text) > 50 else ''}")

        elif content_type == 'image':
            # 上传图片
            import time
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"clipboard_{timestamp}.png"

            # 生成文件哈希
            file_hash = hashlib.sha256(content).hexdigest()

            # 初始化上传
            result = client.call("ft.init_upload", {
                "filename": filename,
                "filesize": len(content),
                "ttl": 86400,  # 24小时
                "download_limit": -1,
                "has_password": False,
                "password": None,
                "e2ee": False,
                "is_public": True,
                "file_hash": file_hash
            })

            upload_url = result['upload_url']
            code = result['code']

            # 上传文件
            response = requests.put(upload_url, data=content)
            response.raise_for_status()

            # 确认上传
            client.call("ft.confirm_upload", {
                "code": code,
                "status": "success"
            })

            # 保存到剪贴板
            client.call("clipboard.copy", {
                "type": "file",
                "file_code": code,
                "filename": filename,
                "size": len(content)
            })

            console.print(f"[bold green]✓ 上传成功[/bold green]")
            console.print(f"  类型: 图片")
            console.print(f"  大小: {humanize.naturalsize(len(content))}")
            console.print(f"  Code: {code}")

    except Exception as e:
        console.print(f"[bold red]✗ 上传失败:[/bold red] {e}")
        raise typer.Exit(1)


@app.command("v")
def view_clipboard():
    """从服务器拉取剪贴板内容，复制到本地剪贴板"""
    config = _load_config()
    client = FiletransClient(config['server_url'], config['api_token'])

    try:
        result = client.call("clipboard.paste", {})

        if result.get("status") == "error":
            console.print(f"[bold yellow]⚠ {result.get('message', '剪贴板为空')}[/bold yellow]")
            raise typer.Exit(0)

        content_type = result.get("type")

        if content_type == "text":
            text = result.get("text")
            console.print(f"[bold green]✓ 已复制到本地剪贴板[/bold green]")
            console.print(f"  类型: 文本")
            console.print(f"  内容: {text[:50]}{'...' if len(text) > 50 else ''}")

            # 复制到本地剪贴板
            _set_system_clipboard('text', text)

        elif content_type == "file":
            code = result.get("code")
            filename = result.get("filename")

            # 下载文件
            get_result = client.call("ft.verify_and_get_link", {"code": code})
            download_url = get_result['download_url']

            response = requests.get(download_url)
            response.raise_for_status()
            file_data = response.content

            # 检测是否为图片
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                console.print(f"[bold green]✓ 已复制到本地剪贴板[/bold green]")
                console.print(f"  类型: 图片")
                console.print(f"  大小: {humanize.naturalsize(len(file_data))}")

                # 复制到本地剪贴板
                _set_system_clipboard('image', file_data)
            else:
                console.print(f"[bold yellow]⚠ 文件 {filename} 不是图片，无法复制到剪贴板[/bold yellow]")
                console.print(f"  请使用 ft get {code} 下载")

    except Exception as e:
        console.print(f"[bold red]✗ 获取失败:[/bold red] {e}")
        raise typer.Exit(1)


@app.command("clear")
def clear_clipboard():
    """清空云端剪贴板"""
    config = _load_config()
    client = FiletransClient(config['server_url'], config['api_token'])

    try:
        result = client.call("clipboard.clear", {})
        console.print(f"[bold green]✓ 剪贴板已清空[/bold green]")
    except Exception as e:
        console.print(f"[bold red]✗ 清空失败:[/bold red] {e}")
        raise typer.Exit(1)


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

    # 设置配置
    os.environ['FT_HOST'] = host
    os.environ['FT_PORT'] = str(port)
    os.environ['FT_STORAGE'] = storage
    os.environ['FT_DATA_DIR'] = data_dir
    os.environ['FT_SERVER_QUOTA'] = server_quota
    os.environ['FT_CLEANUP_INTERVAL'] = str(cleanup_interval)
    os.environ['FT_MAX_SIZE'] = str(max_size)

    # 启动服务器
    from .server.main import serve as start_server
    start_server()


# ==================================================
# 配置命令
# ==================================================

@app.command("config")
def config_cmd(
    action: str = typer.Argument(..., help="操作: show, set"),
    backend: str = typer.Option(None, "--backend", "-b", help="存储后端 (local/s3)"),
    local_dir: str = typer.Option(None, "--local-dir", help="本地存储目录"),
    s3_bucket: str = typer.Option(None, "--s3-bucket", help="S3 Bucket 名称"),
    s3_region: str = typer.Option(None, "--s3-region", help="S3 Region"),
    s3_endpoint: str = typer.Option(None, "--s3-endpoint", help="S3 Endpoint URL"),
    confirm: bool = typer.Option(False, "--confirm", "-y", help="确认清空所有文件")
):
    """管理存储配置（需要管理员权限）"""

    cfg = _load_config()
    client = FiletransClient(cfg['server_url'], cfg['api_token'])

    if action == "show":
        # 显示当前配置
        result = client.call("admin.get_storage_config", {})

        console.print("\n[bold cyan]存储配置[/bold cyan]")
        console.print(f"  后端: [yellow]{result['backend']}[/yellow]")
        console.print(f"  Base URL: {result['base_url']}")

        if result['backend'] == 'LOCAL':
            console.print(f"  存储目录: [cyan]{result['local'].get('root_dir', 'N/A')}[/cyan]")
        elif result['backend'] == 'S3':
            console.print(f"  Bucket: [cyan]{result['s3'].get('bucket', 'N/A')}[/cyan]")
            console.print(f"  Region: {result['s3'].get('region', 'N/A')}")
            console.print(f"  Endpoint: {result['s3'].get('endpoint_url', 'N/A')}")

        console.print()

    elif action == "set":
        if not confirm:
            console.print("[bold red]警告：[/bold red] 修改存储配置会清空所有文件！")
            console.print("请使用 --confirm 或 -y 参数确认。")
            raise typer.Exit(1)

        if not backend:
            console.print("[bold red]错误：[/bold red] 请指定 --backend 参数")
            raise typer.Exit(1)

        config = {
            "backend": backend,
            "confirm": True
        }

        if backend == "local":
            if not local_dir:
                local_dir = typer.prompt("本地存储目录", default="./data/files")
            config["local"] = {"root_dir": local_dir}

        elif backend == "s3":
            if not s3_bucket:
                s3_bucket = typer.prompt("S3 Bucket 名称")
            if not s3_region:
                s3_region = typer.prompt("S3 Region", default="us-east-1")
            if not s3_endpoint:
                s3_endpoint = typer.prompt("S3 Endpoint URL", default="https://s3.amazonaws.com")

            config["s3"] = {
                "bucket": s3_bucket,
                "region": s3_region,
                "endpoint_url": s3_endpoint
            }

        # 发送配置更新请求
        result = client.call("admin.update_storage_config", config)

        if result.get('restarting'):
            console.print(Panel.fit(
                f"[bold green]配置已更新[/bold green]\n\n"
                f"{result['message']}\n\n"
                f"[cyan]服务器正在自动重启...[/cyan]",
                border_style="green"
            ))
            console.print("\n[dim]提示: 如果在 Docker 中运行，容器会自动重启[/dim]")
        else:
            console.print(Panel.fit(
                f"[bold green]配置已更新[/bold green]\n\n"
                f"{result['message']}\n\n"
                f"[yellow]请手动重启服务器以使配置生效[/yellow]",
                border_style="green"
            ))


# ==================================================
# Token 管理命令
# ==================================================

@app.command("token")
def token_cmd(
    action: str = typer.Argument(..., help="操作: list, create, revoke"),
    user_id: str = typer.Option(None, "--user-id", "-u", help="用户 ID（用于 revoke 操作）"),
    label: str = typer.Option(None, "--label", "-l"),
    permissions: str = typer.Option("read,write", "--permissions", "-p"),
    quota: str = typer.Option("10GB", "--quota", "-q")
):
    """管理 API Token（需要管理员权限）"""

    config = _load_config()
    client = FiletransClient(config['server_url'], config['api_token'])

    if action == "list":
        # 列出所有用户
        result = client.call("admin.list_users", {})

        table = Table(title=f"用户列表 - 共 {len(result['users'])} 个用户")
        table.add_column("用户 ID", style="cyan")
        table.add_column("标签", style="white")
        table.add_column("配额使用", style="green")
        table.add_column("状态", style="yellow")
        table.add_column("权限", style="magenta")
        table.add_column("创建时间", style="blue")

        for user in result['users']:
            quota_display = (
                "[green]管理员[/green]" if user['is_admin']
                else f"{humanize.naturalsize(user['quota_current_size'])} / {humanize.naturalsize(user['quota_max_size'])} ({user['quota_used_percent']}%)"
            )
            status_display = "[green]活跃[/green]" if user['is_active'] else "[red]停用[/red]"
            role_display = "[yellow]管理员[/yellow]" if user['is_admin'] else "[dim]普通用户[/dim]"
            created_at = user['created_at'][:10] if user['created_at'] else '-'

            table.add_row(
                user['user_id'],
                user['label'] or user['user_id'],
                quota_display,
                status_display,
                role_display,
                created_at
            )

        console.print(table)

    elif action == "create":
        # 创建新 Token
        quota_bytes = _parse_size(quota)
        user_id_input = typer.prompt("用户 ID", default=f"user_{int(__import__('time').time() * 1000) % 10000}")

        result = client.call("admin.manage_token", {
            "action": "add",
            "config": {
                "user_id": user_id_input,
                "label": label or "User Token",
                "permissions": permissions.split(","),
                "quota_max_size": quota_bytes
            }
        })
        console.print(Panel.fit(
            f"[bold green]新 Token 已创建[/bold green]\n\n"
            f"[bold cyan]{result['token']}[/bold cyan]\n\n"
            f"[yellow]请妥善保管此 Token！[/yellow]",
            border_style="green"
        ))

    elif action == "revoke":
        # 撤销用户
        target_user_id = user_id
        if not target_user_id:
            target_user_id = typer.prompt("输入要撤销的用户 ID")

        result = client.call("admin.manage_token", {
            "action": "revoke",
            "config": {"user_id": target_user_id}
        })
        console.print(f"[bold green]✓ 用户 {target_user_id} 已撤销[/bold green]")


# ==================================================
# 辅助函数
# ==================================================

def _load_config() -> dict:
    """加载配置"""
    if not CONFIG_FILE.exists():
        console.print("[bold red]✗ 未找到配置文件，请先运行 'ft init'[/bold red]")
        raise typer.Exit(1)

    with open(CONFIG_FILE) as f:
        return json.load(f)


def _parse_ttl(ttl: str) -> int:
    """解析 TTL 字符串"""
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
    match = re.match(r'([\d.]+)([KMGT]?B?)', size.upper())
    if not match:
        raise ValueError(f"Invalid size format: {size}")

    value, unit = match.groups()
    value = float(value)

    multipliers = {
        'B': 1,
        'KB': 1024,
        'MB': 1024**2,
        'GB': 1024**3,
        'TB': 1024**4
    }

    return int(value * multipliers.get(unit, 1))


# ==================================================
# 错误处理包装器
# ==================================================

def cli_with_error_handling():
    """带错误处理的 CLI 入口"""
    import sys
    try:
        app()
    except SystemExit:
        raise
    except Exception as e:
        console.print(f"\n[bold red]错误:[/bold red] {str(e)}\n")
        console.print("[dim]运行 'ft help' 查看所有可用命令[/dim]\n")
        raise typer.Exit(1)


# 导出的入口点
main = cli_with_error_handling


if __name__ == "__main__":
    main()
