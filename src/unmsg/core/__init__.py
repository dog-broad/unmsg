"""UnMsg conversion core — pure Python, no UI, no import-time side effects."""

from __future__ import annotations

from unmsg.core.batch import convert_batch
from unmsg.core.models import Attachment, ConvertResult, MsgRecord
from unmsg.core.options import ConvertOptions
from unmsg.core.pipeline import convert_file

__all__ = [
    "Attachment",
    "ConvertOptions",
    "ConvertResult",
    "MsgRecord",
    "convert_batch",
    "convert_file",
]
