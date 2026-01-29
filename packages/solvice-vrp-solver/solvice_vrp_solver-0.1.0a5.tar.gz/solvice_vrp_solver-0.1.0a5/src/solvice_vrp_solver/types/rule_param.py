# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo
from .period_param import PeriodParam

__all__ = ["RuleParam"]


class RuleParam(TypedDict, total=False):
    """Periodic time rule for a resource"""

    job_type_limitations: Annotated[Optional[Dict[str, int]], PropertyInfo(alias="jobTypeLimitations")]
    """Map of job type to maximum count allowed per period. Null means no limitations."""

    max_drive_time: Annotated[Optional[int], PropertyInfo(alias="maxDriveTime")]
    """Maximum drive time in seconds"""

    max_job_complexity: Annotated[Optional[int], PropertyInfo(alias="maxJobComplexity")]
    """
    Sum of the complexity of the jobs completed by this resource should not go over
    this value
    """

    max_service_time: Annotated[Optional[int], PropertyInfo(alias="maxServiceTime")]
    """Maximum service time in seconds"""

    max_work_time: Annotated[Optional[int], PropertyInfo(alias="maxWorkTime")]
    """Maximum work time in seconds. Work time is service time + drive/travel time."""

    min_drive_time: Annotated[Optional[int], PropertyInfo(alias="minDriveTime")]
    """Minimum drive time in seconds"""

    min_job_complexity: Annotated[Optional[int], PropertyInfo(alias="minJobComplexity")]
    """
    Sum of the complexity of the jobs completed by this resource should reach this
    value
    """

    min_service_time: Annotated[Optional[int], PropertyInfo(alias="minServiceTime")]
    """Minimum service time in seconds"""

    min_work_time: Annotated[Optional[int], PropertyInfo(alias="minWorkTime")]
    """Minimum work time in seconds. Work time is service time + drive/travel time."""

    period: Optional[PeriodParam]
    """Subset of the planning period"""
