"""UnMsg — turn Outlook ``.msg`` files into clean, readable formats.

Importing this package pulls in only the conversion core (no Qt, no GUI).

The public API is intentionally small and **stable from 1.0 onward**. Anything
not listed in :data:`__all__` is internal and may change without notice. Within
``1.x``:

* The seven names below keep their identities and shapes.
* :class:`ConvertOptions` and the data models (:class:`Attachment`,
  :class:`MsgRecord`, :class:`ConvertResult`) gain new *optional* fields only.
* :func:`convert_file` and :func:`convert_batch` keep their existing keyword
  arguments; new optional arguments may be added at the tail.

Anything outside this contract — submodules of :mod:`unmsg.core`, writer
internals, the UI, the CLI module layout — is private and not covered by the
stability promise.
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
