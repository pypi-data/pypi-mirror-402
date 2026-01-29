"""GoXLR Utility API: Helpers"""
from __future__ import annotations

import logging
from typing import Optional

from ..const import VOLUME_MAX
from ..models.patch import Patch
from ..models.status import Mixer, Status

_LOGGER = logging.getLogger(__name__)


def get_mixer_from_status(status: Status) -> Optional[Mixer]:
    """Get first mixer from status"""
    return next(iter(status.mixers.values()), None)


def get_volume_percentage(
    mixer: Mixer,
    key: str,
) -> Optional[int]:
    """Return the volume in percent."""
    if (value := getattr(mixer.levels.volumes, key, None)) is not None:
        return round(value / VOLUME_MAX * 100)
    return None


def get_attribute_names_from_patch(
    data: Mixer,
    patch: Patch,
) -> list[str]:
    """Get attribute names from patch"""
    paths = patch.path.split("/")
    if len(paths) <= 3 or paths[1] != "mixers":
        _LOGGER.debug("Unused patch received: %s: %s", paths, patch.value)
        raise ValueError("Unused patch received")

    current_attribute = data
    current_path = ""
    attribute_names = []
    for path in paths[3:]:
        alias = None
        for field_name, field in current_attribute.__fields__.items():
            if field.alias == path:
                alias = field_name
                break
        _LOGGER.debug(
            "Getting path for '%s' ('%s'): %s",
            path,
            alias,
            type(current_attribute),
        )
        current_path = alias or path
        current_attribute = getattr(current_attribute, current_path)
        attribute_names.append(current_path)

    return attribute_names
