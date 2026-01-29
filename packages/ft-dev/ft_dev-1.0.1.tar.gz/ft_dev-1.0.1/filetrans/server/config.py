"""
filetrans configuration management
"""

import os
import secrets
from pathlib import Path


def get_config_path() -> Path:
    """获取配置文件路径"""
    # 优先使用环境变量指定的配置文件
    config_file = os.environ.get('FT_CONFIG_FILE')
    if config_file:
        return Path(config_file)

    # 默认在当前目录查找 filetrans.json
    return Path.cwd() / 'filetrans.json'


def generate_admin_token() -> str:
    """生成管理员 Token"""
    return f"ft_admin_{secrets.token_urlsafe(32)}"


def generate_user_token() -> str:
    """生成用户 Token"""
    return f"ft_{secrets.token_urlsafe(32)}"


def get_config() -> dict:
    """获取配置"""
    host = os.environ.get('FT_HOST', '0.0.0.0')
    port = int(os.environ.get('FT_PORT', 8866))

    # 对于 base_url，使用 localhost 而不是 0.0.0.0
    base_url = os.environ.get('FT_BASE_URL', f'http://localhost:{port}')

    return {
        'server': {
            'host': host,
            'port': port,
        },
        'storage': {
            'backend': os.environ.get('FT_STORAGE', 'LOCAL'),
            'local': {
                'root_dir': os.environ.get('FT_DATA_DIR', './data/files'),
            },
            's3': {
                'bucket': os.environ.get('FT_S3_BUCKET', ''),
                'region': os.environ.get('FT_S3_REGION', 'us-east-1'),
                'endpoint_url': os.environ.get('FT_S3_ENDPOINT', 'https://s3.amazonaws.com'),
            },
            'base_url': base_url,
        },
        'janitor': {
            'interval_seconds': int(os.environ.get('FT_CLEANUP_INTERVAL', 60)),
            'disk_threshold_percent': int(os.environ.get('FT_DISK_THRESHOLD', 10)),
        },
        'security': {
            'max_file_size': int(os.environ.get('FT_MAX_SIZE', 512 * 1024 * 1024)),
            'server_quota_bytes': _parse_size(os.environ.get('FT_SERVER_QUOTA', '100GB')),
        }
    }


def _parse_size(size_str: str) -> int:
    """解析大小字符串"""
    size_str = size_str.strip().upper()
    if size_str.endswith('TB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    else:
        return int(size_str)
