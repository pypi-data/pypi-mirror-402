# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional

from pydantic import Field as FieldInfo

from .period import Period
from .._models import BaseModel

__all__ = ["Rule"]


class Rule(BaseModel):
    """Periodic time rule for a resource"""

    job_type_limitations: Optional[Dict[str, int]] = FieldInfo(alias="jobTypeLimitations", default=None)
    """Map of job type to maximum count allowed per period. Null means no limitations."""

    max_drive_time: Optional[int] = FieldInfo(alias="maxDriveTime", default=None)
    """Maximum drive time in seconds"""

    max_job_complexity: Optional[int] = FieldInfo(alias="maxJobComplexity", default=None)
    """
    Sum of the complexity of the jobs completed by this resource should not go over
    this value
    """

    max_service_time: Optional[int] = FieldInfo(alias="maxServiceTime", default=None)
    """Maximum service time in seconds"""

    max_work_time: Optional[int] = FieldInfo(alias="maxWorkTime", default=None)
    """Maximum work time in seconds. Work time is service time + drive/travel time."""

    min_drive_time: Optional[int] = FieldInfo(alias="minDriveTime", default=None)
    """Minimum drive time in seconds"""

    min_job_complexity: Optional[int] = FieldInfo(alias="minJobComplexity", default=None)
    """
    Sum of the complexity of the jobs completed by this resource should reach this
    value
    """

    min_service_time: Optional[int] = FieldInfo(alias="minServiceTime", default=None)
    """Minimum service time in seconds"""

    min_work_time: Optional[int] = FieldInfo(alias="minWorkTime", default=None)
    """Minimum work time in seconds. Work time is service time + drive/travel time."""

    period: Optional[Period] = None
    """Subset of the planning period"""
