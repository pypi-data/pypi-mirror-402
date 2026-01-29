# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .location import Location

__all__ = ["Shift", "Break"]


class Break(BaseModel):
    type: Literal["WINDOWED", "DRIVE", "UNAVAILABILITY"]
    """Type of break that can be defined for a resource"""


class Shift(BaseModel):
    """Shift definition.

    Every potential shift of a resource should be defined here. Every shift can be a trip.
    """

    from_: str = FieldInfo(alias="from")
    """Start of the shift datetime"""

    to: str
    """End of the shift datetime"""

    breaks: Optional[List[Break]] = None
    """Windowed breaks definitions."""

    end: Optional[Location] = None
    """Geographical Location in WGS-84"""

    ignore_travel_time_from_last_job: Optional[bool] = FieldInfo(alias="ignoreTravelTimeFromLastJob", default=None)
    """Ignore the travel time from the last order to the optional end location"""

    ignore_travel_time_to_first_job: Optional[bool] = FieldInfo(alias="ignoreTravelTimeToFirstJob", default=None)
    """Ignore the travel time from the start location to the first order"""

    job_type_limitations: Optional[Dict[str, int]] = FieldInfo(alias="jobTypeLimitations", default=None)
    """Map of job type to maximum count allowed per shift. Null means no limitations."""

    overtime: Optional[object] = None
    """Can go into overtime."""

    overtime_end: Optional[str] = FieldInfo(alias="overtimeEnd", default=None)
    """Maximum overtime time."""

    start: Optional[Location] = None
    """Geographical Location in WGS-84"""

    tags: Optional[List[str]] = None
    """
    Shift tags will ensure that this resource can only do Jobs of this tag during
    this shift. This allows for tag based availability.
    """
