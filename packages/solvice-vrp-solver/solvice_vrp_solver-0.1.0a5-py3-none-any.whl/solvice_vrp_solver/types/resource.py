# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .rule import Rule
from .shift import Shift
from .._models import BaseModel
from .location import Location

__all__ = ["Resource"]


class Resource(BaseModel):
    """Resource (vehicle, employee)"""

    name: str
    """Unique identifier for this resource.

    Used to reference the resource in job assignments, relations, and results. Must
    be unique within the request.
    """

    shifts: Optional[List[Shift]] = None
    """List of work shifts defining when this resource is available for job
    assignments.

    Each shift specifies working hours, start/end locations, breaks, and other
    constraints. Multiple shifts allow for multi-day planning or split-shift
    schedules. At least one shift is required.
    """

    capacity: Optional[List[int]] = None
    """
    Multi-dimensional capacity limits for this resource, such as weight, volume, or
    item count. Each dimension corresponds to job load requirements. For example,
    [500, 200] might represent 500 kg weight capacity and 200 cubic meters volume
    capacity. Maximum 5 dimensions supported.
    """

    category: Optional[Literal["CAR", "BIKE", "TRUCK"]] = None
    """Transportation type for the resource"""

    compatible_resources: Optional[List[str]] = FieldInfo(alias="compatibleResources", default=None)
    """
    List of resource names that this resource is compatible to work with on linked
    jobs requiring cooperation
    """

    end: Optional[Location] = None
    """Geographical Location in WGS-84"""

    hourly_cost: Optional[int] = FieldInfo(alias="hourlyCost", default=None)
    """Hourly cost rate for this resource in your currency units.

    Used to calculate total labor costs for solutions. Only counts active time
    (driving, servicing, or waiting), not idle time. This enables cost-based
    optimization and financial analysis of routing solutions.
    """

    max_drive_distance: Optional[int] = FieldInfo(alias="maxDriveDistance", default=None)
    """Maximum total distance allowed for this resource per shift or planning period.

    This constraint prevents excessive driving and ensures compliance with
    regulations or operational policies. Measured in meters and includes all travel
    between jobs but excludes service time.
    """

    max_drive_time: Optional[int] = FieldInfo(alias="maxDriveTime", default=None)

    max_drive_time_in_seconds: Optional[object] = FieldInfo(alias="maxDriveTimeInSeconds", default=None)
    """
    Maximum total driving time allowed for this resource per shift or planning
    period. This constraint prevents excessive driving and ensures compliance with
    regulations or operational policies. Measured in seconds and includes all travel
    between jobs but excludes service time.
    """

    max_drive_time_job: Optional[int] = FieldInfo(alias="maxDriveTimeJob", default=None)

    region: Optional[Location] = None
    """Geographical Location in WGS-84"""

    rules: Optional[List[Rule]] = None
    """
    List of periodic constraints that apply to this resource over specified time
    periods. Rules can enforce minimum/maximum work time, service time, drive time,
    or job complexity limits. These constraints ensure compliance with labor
    regulations, operational policies, or capacity limitations.
    """

    start: Optional[Location] = None
    """Geographical Location in WGS-84"""

    tags: Optional[List[str]] = None
    """List of capability tags that define what types of jobs this resource can
    perform.

    Tags create matching constraints between jobs and resources - only resources
    with matching tags can be assigned to jobs that require those capabilities. For
    example, 'plumbing' or 'electrical' tags.
    """
