"""GoXLR Utility API: Map Model"""

from __future__ import annotations

from dataclasses import dataclass

from . import DefaultBaseModel


@dataclass
class MapItem(DefaultBaseModel):
    """GoXLR Utility API: Map Item Model"""

    key: str = ""
    name: str = ""
    icon: str = ""
