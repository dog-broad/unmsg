"""UnMsg — turn Outlook ``.msg`` files into clean, readable formats.

Importing this package pulls in only the conversion core (no Qt, no GUI). The
public API is intentionally small and stable.
"""

from __future__ import annotations

from unmsg._version import __version__
from unmsg.core import (
    Attachment,
    ConvertOptions,
    ConvertResult,
    MsgRecord,
    convert_batch,
    convert_file,
)

__all__ = [
    "Attachment",
    "ConvertOptions",
    "ConvertResult",
    "MsgRecord",
    "__version__",
    "convert_batch",
    "convert_file",
]
