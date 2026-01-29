# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["Weights"]


class Weights(BaseModel):
    """OnRoute Weights"""

    allowed_resources_weight: Optional[int] = FieldInfo(alias="allowedResourcesWeight", default=None)
    """Weight modifier for soft violations of resource assignment constraints.

    When jobs have allowedResources restrictions and they cannot be satisfied as
    hard constraints, this weight determines the penalty for assigning jobs to
    non-allowed resources.
    """

    asap_weight: Optional[int] = FieldInfo(alias="asapWeight", default=None)
    """
    Weight modifier for scheduling jobs as early as possible within their time
    windows and resource availability. Higher values push jobs toward the beginning
    of shifts and planning periods, useful for front-loading work or maximizing
    completion rates.
    """

    clustering_weight: Optional[int] = FieldInfo(alias="clusteringWeight", default=None)
    """Weight modifier for geographic clustering constraint.

    Controls the penalty for route bounding box overlaps when clustering is enabled.
    Higher values more strongly discourage routes from overlapping in geographic
    space, promoting clearer territorial separation. The penalty is multiplied by
    this weight before being applied to the score.
    """

    drive_time_weight: Optional[int] = FieldInfo(alias="driveTimeWeight", default=None)
    """Weight modifier for total driving time across all resources.

    Similar to travelTimeWeight but focuses specifically on driving time violations
    or constraints. Higher values make the solver more concerned with minimizing
    driving time, useful for fuel efficiency or driver fatigue management.
    """

    job_proximity_weight: Optional[int] = FieldInfo(alias="jobProximityWeight", default=None)
    """Weight modifier for separating jobs that are geographically close to each other.

    When jobProximityRadius is set in options, this weight penalizes consecutive
    scheduling of jobs within that radius to different resources or non-consecutive
    scheduling. Higher values encourage grouping nearby jobs together in the same
    route segment.
    """

    minimize_resources_weight: Optional[int] = FieldInfo(alias="minimizeResourcesWeight", default=None)
    """Weight modifier for minimizing the number of active resources per day/trip.

    The weight is measured in the same units as travel time - a weight of 3600 means
    using an additional resource is equivalent to 1 hour of travel time. Higher
    values encourage consolidation of jobs onto fewer resources.
    """

    planned_weight: Optional[int] = FieldInfo(alias="plannedWeight", default=None)
    """Weight modifier for deviations from planned arrivals and resource assignments.

    Higher values make the solver more reluctant to deviate from plannedArrival
    times and plannedResource assignments. This is crucial for maintaining customer
    appointments and commitments.
    """

    priority_weight: Optional[int] = FieldInfo(alias="priorityWeight", default=None)
    """Weight modifier for job priority constraints.

    Higher values make the solver more likely to include high-priority jobs in the
    solution when not all jobs can be assigned. This affects job selection
    probability but not scheduling order. The weight is multiplied by the job's
    priority value and duration.
    """

    ranking_weight: Optional[int] = FieldInfo(alias="rankingWeight", default=None)
    """Weight modifier for resource ranking preferences defined in job rankings.

    Higher values make the solver more aggressive about assigning jobs to their
    preferred (lower-ranked) resources, even if it increases travel time or other
    costs. This helps maintain service quality by using optimal resource
    assignments.
    """

    travel_time_weight: Optional[int] = FieldInfo(alias="travelTimeWeight", default=None)
    """Weight modifier for total travel time optimization.

    This is the baseline weight (typically 1) against which all other weights are
    compared. Higher values make the solver more aggressive about minimizing travel
    time, potentially at the expense of other objectives.
    """

    urgency_weight: Optional[int] = FieldInfo(alias="urgencyWeight", default=None)
    """Weight modifier for job urgency constraints.

    Higher values make the solver more aggressive about scheduling urgent jobs
    earlier in the day and planning period. This affects the sequence and timing of
    job execution based on their urgency values.
    """

    wait_time_weight: Optional[int] = FieldInfo(alias="waitTimeWeight", default=None)
    """Weight modifier for total waiting time across all resources.

    Waiting time occurs when resources arrive at jobs before their time windows open
    or when they have idle time between jobs. Higher values make the solver more
    aggressive about minimizing idle time.
    """

    workload_spread_weight: Optional[int] = FieldInfo(alias="workloadSpreadWeight", default=None)
    """Weight modifier for workload balancing across resources and time periods.

    Higher values make the solver more aggressive about equalizing service time
    distribution. Works with fairWorkloadPerTrip and fairWorkloadPerResource
    options, and is sensitive to the workloadSensitivity parameter.
    """
