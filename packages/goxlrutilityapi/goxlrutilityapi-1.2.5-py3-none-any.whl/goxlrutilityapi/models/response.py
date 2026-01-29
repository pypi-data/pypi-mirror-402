"""GoXLR Utility API: Response Model"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, Optional, TypeVar

from . import DefaultBaseModel

T = TypeVar("T")


@dataclass
class Response(DefaultBaseModel, Generic[T]):
    """Response Model"""

    id: str
    result: Any
    jsonrpc: str = "2.0"
    error: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None
