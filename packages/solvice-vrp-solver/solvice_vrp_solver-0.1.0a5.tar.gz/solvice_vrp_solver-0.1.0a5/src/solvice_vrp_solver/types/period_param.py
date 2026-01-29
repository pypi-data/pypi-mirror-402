# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import datetime
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["PeriodParam"]

_PeriodParamReservedKeywords = TypedDict(
    "_PeriodParamReservedKeywords",
    {
        "from": Union[str, datetime],
    },
    total=False,
)


class PeriodParam(_PeriodParamReservedKeywords, total=False):
    """Subset of the planning period"""

    end: Required[object]
    """End date-time"""

    to: Required[Annotated[Union[str, datetime], PropertyInfo(format="iso8601")]]
