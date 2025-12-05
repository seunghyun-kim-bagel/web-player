"""
Web Player - 설정 관리
"""
import os
from dataclasses import dataclass
from typing import Optional


def get_env(key: str, default: str = None) -> Optional[str]:
    """환경 변수 읽기"""
    return os.environ.get(key, default)


def get_env_int(key: str, default: int) -> int:
    """환경 변수를 정수로 읽기"""
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_env_bool(key: str, default: bool) -> bool:
    """환경 변수를 불리언으로 읽기"""
    value = os.environ.get(key)
    if value is None:
        return default
    return value.lower() in ('true', '1', 'yes', 'on')


@dataclass
class Settings:
    """애플리케이션 설정"""

    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 8000

    # Screen Capture
    screen_fps: int = 30
    screen_quality: int = 70
    screen_format: str = "JPEG"

    # Security
    enable_auth: bool = False
    auth_token: Optional[str] = None

    # WebSocket
    ws_ping_interval: int = 30
    ws_ping_timeout: int = 10

    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = "logs/server.log"

    # UI-TARS / OpenAI
    openai_api_key: Optional[str] = None
    uitars_model: str = "gpt-4o"
    uitars_mock_mode: bool = False  # 테스트용 Mock 모드

    @classmethod
    def from_env(cls) -> "Settings":
        """환경 변수에서 설정 로드"""
        return cls(
            server_host=get_env("SERVER_HOST", "0.0.0.0"),
            server_port=get_env_int("SERVER_PORT", 8000),
            screen_fps=get_env_int("SCREEN_FPS", 30),
            screen_quality=get_env_int("SCREEN_QUALITY", 70),
            screen_format=get_env("SCREEN_FORMAT", "JPEG"),
            enable_auth=get_env_bool("ENABLE_AUTH", False),
            auth_token=get_env("AUTH_TOKEN"),
            ws_ping_interval=get_env_int("WS_PING_INTERVAL", 30),
            ws_ping_timeout=get_env_int("WS_PING_TIMEOUT", 10),
            log_level=get_env("LOG_LEVEL", "INFO"),
            log_file=get_env("LOG_FILE", "logs/server.log"),
            openai_api_key=get_env("OPENAI_API_KEY"),
            uitars_model=get_env("UITARS_MODEL", "gpt-4o"),
            uitars_mock_mode=get_env_bool("UITARS_MOCK_MODE", False),
        )


# 전역 설정 인스턴스
settings = Settings.from_env()
