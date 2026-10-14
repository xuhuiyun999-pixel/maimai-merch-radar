import os
from pathlib import Path


class LocalInputError(ValueError):
    """Fixed, locally authored validation messages safe to display."""


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_token(project_root: Path) -> str:
    token = os.environ.get('MCD_MCP_TOKEN', '').strip()
    if not token:
        env_file = project_root / '.env'
        if env_file.is_file():
            for line in env_file.read_text(encoding='utf-8-sig').splitlines():
                key, _, value = line.partition('=')
                if key.strip() == 'MCD_MCP_TOKEN':
                    token = value.strip().strip('\"\'')
                    break
    if not token or '\n' in token or '\r' in token:
        raise LocalInputError('请先在本机运行 maimai-radar configure 配置连接凭据。')
    return token
