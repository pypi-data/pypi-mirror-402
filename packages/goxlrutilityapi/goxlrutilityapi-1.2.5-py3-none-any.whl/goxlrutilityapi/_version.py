"""Version information for goxlrutilityapi"""


class Version:
    """Version class to maintain compatibility with incremental-style version access"""

    def __init__(self, version_string: str) -> None:
        self.version_string = version_string

    def public(self) -> str:
        """Return the public version string"""
        return self.version_string

    def __str__(self) -> str:
        return self.version_string


__version__ = Version("1.2.5.dev0")
