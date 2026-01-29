# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, TypedDict

__all__ = ["WindowParam"]

_WindowParamReservedKeywords = TypedDict(
    "_WindowParamReservedKeywords",
    {
        "from": str,
    },
    total=False,
)


class WindowParam(_WindowParamReservedKeywords, total=False):
    """Window in which the job can be executed"""

    to: Required[str]
    """Date time end of window"""

    hard: Optional[bool]
    """Hard constraint violation of DateWindow"""

    weight: Optional[int]
    """Weight constraint modifier"""
