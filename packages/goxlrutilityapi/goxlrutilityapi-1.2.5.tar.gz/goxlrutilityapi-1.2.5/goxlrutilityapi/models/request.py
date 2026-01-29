"""GoXLR Utility API: Request Model"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from . import DefaultBaseModel


@dataclass
class Request(DefaultBaseModel):
    """Request Model"""

    id: str
    method: str
    params: dict[str, Any]
    jsonrpc: str = "2.0"
    metadata: Optional[dict[str, Any]] = None
