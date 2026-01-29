"""GoXLR Utility API: Patch Models"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from . import DefaultBaseModel


@dataclass
class Patch(DefaultBaseModel):
    """Patch Model"""

    op: str
    path: str
    value: Any
    from_value: Optional[Any] = None
    metadata: Optional[dict[str, Any]] = None


@dataclass
class Data(DefaultBaseModel):
    """Data Model"""

    patch: list[Patch] = field(metadata={"alias": "Patch"})
