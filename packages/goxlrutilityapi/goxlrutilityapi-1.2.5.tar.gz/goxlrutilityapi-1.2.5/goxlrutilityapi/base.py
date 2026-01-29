"""GoXLR Utility API: Base"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Base:
    """GoXLR Utility API: Base Model"""

    id: str
    jsonrpc: str = "2.0"
    metadata: Optional[dict[str, Any]] = None

    def __post_init__(self):
        """Initialize"""
        name = f"{self.__module__}.{self.__class__.__name__}"
        self._logger = logging.getLogger(name)
        self._logger.debug("%s __init__", name)
