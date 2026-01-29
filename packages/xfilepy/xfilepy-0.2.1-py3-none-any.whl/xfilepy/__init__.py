"""
Cross‑platform (Android / iOS / Desktop) file handling library.

Design goals:
    typed public surface, explicit platform modules, zero side effects at
    import, late binding to the active platform, and no runtime deps for
    platforms you don’t use.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._base import _BaseFileHandler
from ._platform import current_platform

__all__ = ["FileHandler"]
__version__ = "0.1.0"
__docformat__ = "google"

if TYPE_CHECKING:
    FileHandler = _BaseFileHandler
else:
    _platform = current_platform()
    if _platform == "android":
        from .android import FileHandler
    elif _platform == "ios":
        from .ios import FileHandler
    else:
        from .desktop import FileHandler
