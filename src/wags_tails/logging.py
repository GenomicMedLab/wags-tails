"""Configure application logging."""

import logging


def initialize_logs(log_level: int = logging.DEBUG) -> None:
    """Configure logging for application-level uses.

    :param log_level: app log level to set
    """
    logging.basicConfig(
        filename=f"{__package__}.log",
        format="[%(asctime)s] - %(name)s - %(levelname)s : %(message)s",
    )
    logger = logging.getLogger(__package__)
    logger.setLevel(log_level)
