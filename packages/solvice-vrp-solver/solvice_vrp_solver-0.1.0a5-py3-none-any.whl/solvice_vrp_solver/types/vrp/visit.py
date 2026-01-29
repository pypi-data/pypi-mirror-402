# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ..._models import BaseModel
from ..location import Location

__all__ = ["Visit"]


class Visit(BaseModel):
    """Single visit for a resource.

    Holds information of the actual arrival time, the job, the location and the latlng.
    """

    activity: Optional[str] = None
    """The activity to"""

    arrival: Optional[datetime] = None
    """Actual arrival date-time"""

    break_time: Optional[int] = FieldInfo(alias="breakTime", default=None)
    """Break time in seconds"""

    distance: Optional[int] = None
    """Total travel distance to that job in meters"""

    job: Optional[str] = None
    """Job"""

    latlon: Optional[List[float]] = None
    """Snapped Latlng.

    When we get your lat/lon in input, we snap it on our map to a valid point in the
    graph. We return all snapped points.
    """

    location: Optional[Location] = None
    """Geographical Location in WGS-84"""

    service_time: Optional[int] = FieldInfo(alias="serviceTime", default=None)
    """Total service time of that job in seconds"""

    snapped_location: Optional[Location] = FieldInfo(alias="snappedLocation", default=None)
    """Geographical Location in WGS-84"""

    travel_time: Optional[int] = FieldInfo(alias="travelTime", default=None)
    """Total travel time to that job in seconds"""

    wait_time: Optional[int] = FieldInfo(alias="waitTime", default=None)
    """Wait time in seconds"""
