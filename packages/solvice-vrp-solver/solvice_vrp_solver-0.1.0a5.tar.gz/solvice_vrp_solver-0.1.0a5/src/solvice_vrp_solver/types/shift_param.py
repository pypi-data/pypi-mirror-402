# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Iterable, Optional
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo
from .location_param import LocationParam

__all__ = ["ShiftParam", "Break"]


class Break(TypedDict, total=False):
    type: Required[Literal["WINDOWED", "DRIVE", "UNAVAILABILITY"]]
    """Type of break that can be defined for a resource"""


_ShiftParamReservedKeywords = TypedDict(
    "_ShiftParamReservedKeywords",
    {
        "from": str,
    },
    total=False,
)


class ShiftParam(_ShiftParamReservedKeywords, total=False):
    """Shift definition.

    Every potential shift of a resource should be defined here. Every shift can be a trip.
    """

    to: Required[str]
    """End of the shift datetime"""

    breaks: Optional[Iterable[Break]]
    """Windowed breaks definitions."""

    end: Optional[LocationParam]
    """Geographical Location in WGS-84"""

    ignore_travel_time_from_last_job: Annotated[Optional[bool], PropertyInfo(alias="ignoreTravelTimeFromLastJob")]
    """Ignore the travel time from the last order to the optional end location"""

    ignore_travel_time_to_first_job: Annotated[Optional[bool], PropertyInfo(alias="ignoreTravelTimeToFirstJob")]
    """Ignore the travel time from the start location to the first order"""

    job_type_limitations: Annotated[Optional[Dict[str, int]], PropertyInfo(alias="jobTypeLimitations")]
    """Map of job type to maximum count allowed per shift. Null means no limitations."""

    overtime: object
    """Can go into overtime."""

    overtime_end: Annotated[Optional[str], PropertyInfo(alias="overtimeEnd")]
    """Maximum overtime time."""

    start: Optional[LocationParam]
    """Geographical Location in WGS-84"""

    tags: Optional[SequenceNotStr[str]]
    """
    Shift tags will ensure that this resource can only do Jobs of this tag during
    this shift. This allows for tag based availability.
    """
