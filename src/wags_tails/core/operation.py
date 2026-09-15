"""Provide session-wide configuration"""

import logging
from dataclasses import dataclass

DEFAULT_HTTP_TIMEOUT = 30
DEFAULT_HTTP_RETRIES = 3

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OperationConfig:
    """Configure session-wide parameters"""

    show_progress: bool = True
    timeout: float = DEFAULT_HTTP_TIMEOUT
    retries: int = DEFAULT_HTTP_RETRIES

    def __post_init__(self) -> None:
        """Log the configured HTTP operation policy."""
        logger.debug(
            "Configured HTTP operations: timeout=%s, retries=%d, show_progress=%s",
            self.timeout,
            self.retries,
            self.show_progress,
        )
