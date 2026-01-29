"""GoXLR Utility API: Models"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DefaultBaseModel:
    """Default Base Model"""

    _extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Handle extra fields"""
        for key, value in self.__dict__.items():
            if key.startswith("_"):
                continue
            if not hasattr(self, key):
                self._extra[key] = value
                delattr(self, key)
