
import sys


if sys.version_info < (3, 11):
    import enum

    class StrEnum(str, enum.Enum):
        """Backport of enum.StrEnum from Python 3.11."""
        pass
else:
    from enum import StrEnum

__all__ = ("StrEnum")
