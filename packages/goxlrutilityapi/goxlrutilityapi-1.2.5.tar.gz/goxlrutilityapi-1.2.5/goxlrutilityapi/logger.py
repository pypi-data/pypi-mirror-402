"""GoXLR Utility API: Logger"""

import logging
from dataclasses import dataclass
from typing import Any, Final, Optional

DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"
FORMAT: Final[str] = "%(asctime)s %(levelname)s (%(threadName)s) [%(name)s] %(message)s"


@dataclass
class Logger:
    """GoXLR Utility API: Logger Model"""

    name: str
    level: int
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    metadata: Optional[dict[str, Any]] = None


def setup_logger(
    log_level: str = "INFO",
) -> logging.Logger:
    """Set up logging"""

    logging.basicConfig(
        datefmt=DATE_FORMAT,
        format=FORMAT,
        level=log_level,
    )

    logger = logging.getLogger("")
    logger.setLevel(log_level)

    return logger
