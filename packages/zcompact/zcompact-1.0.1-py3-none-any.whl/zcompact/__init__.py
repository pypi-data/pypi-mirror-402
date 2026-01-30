"""
zcompact - Python wrapper for the zcompact CLI tool.

JSON compaction with queryable ID index.
"""

from .archive import Archive
from .exceptions import ZcompactError, RecordNotFoundError, ArchiveError

__version__ = "1.0.1"
__all__ = ["Archive", "ZcompactError", "RecordNotFoundError", "ArchiveError"]
