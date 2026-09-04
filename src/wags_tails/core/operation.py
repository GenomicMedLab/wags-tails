"""Provide session-wide configuration"""

from dataclasses import dataclass

DEFAULT_HTTP_TIMEOUT = 30
DEFAULT_HTTP_RETRIES = 3


@dataclass(frozen=True)
class OperationConfig:
    """Configure session-wide parameters"""

    show_progress: bool = True
    timeout: float = DEFAULT_HTTP_TIMEOUT
    retries: int = DEFAULT_HTTP_RETRIES
