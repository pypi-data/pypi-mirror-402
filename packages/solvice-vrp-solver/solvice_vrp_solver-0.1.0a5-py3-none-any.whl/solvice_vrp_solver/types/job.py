# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from .window import Window
from .._models import BaseModel
from .location import Location

__all__ = ["Job", "Proficiency", "Ranking", "Tag"]


class Proficiency(BaseModel):
    """Defines how efficiently a specific resource can complete a job.

    The durationModifier adjusts the job's effective service time when assigned to that resource.
    """

    resource: str
    """Name of the resource whose proficiency is being defined.

    Must exactly match a resource name defined in the request's resources list.
    """

    duration_modifier: Optional[float] = FieldInfo(alias="durationModifier", default=None)
    """Multiplier applied to the job's duration when assigned to this resource.

    Values less than 1.0 reduce the duration (faster completion), values greater
    than 1.0 increase it (slower completion). For example, 0.8 means the resource
    completes the job 20% faster, 1.5 means 50% slower. Default is 1.0 (no
    modification).
    """


class Ranking(BaseModel):
    """A ranking is a measure of the affinity of a `Resource` towards a `Job`."""

    name: str
    """Name of the resource being ranked for this job.

    Must exactly match a resource name defined in the request's resources list. This
    creates a preference relationship between the job and the specified resource.
    """

    ranking: Optional[int] = None
    """Preference ranking score for this resource (1-100).

    Lower values indicate stronger preference - rank 1 is most preferred, rank 100
    is least preferred. The solver will try to assign jobs to higher-ranked
    (lower-numbered) resources when possible, with the preference strength
    controlled by the rankingWeight in the weights configuration.
    """


class Tag(BaseModel):
    """A tag is a match between a `Job` and a `Resource`."""

    name: str
    """Tag name that defines a skill, capability, or requirement.

    This creates a matching constraint between jobs and resources - only resources
    with this tag can be assigned to jobs that require it. Common examples include
    'plumbing', 'electrical', 'certified-technician', or 'heavy-lifting'.
    """

    hard: Optional[bool] = None
    """Constraint type for this tag requirement.

    When true (default), creates a hard constraint - jobs can only be assigned to
    resources with matching tags. When false, creates a soft constraint - jobs
    prefer resources with matching tags but can be assigned to others if needed,
    with a score penalty.
    """

    weight: Optional[int] = None
    """
    Penalty weight applied when this tag constraint is violated (soft constraints
    only). The weight is measured in the same units as travel time - a weight of
    3600 means violating this tag constraint is equivalent to 1 hour of additional
    travel time. Higher weights make the constraint more important.
    """


class Job(BaseModel):
    """A job to be performed by a resource."""

    name: str
    """Unique description"""

    allowed_resources: Optional[List[str]] = FieldInfo(alias="allowedResources", default=None)
    """List of vehicle names that are allowed to be assigned to this order."""

    complexity: Optional[int] = None
    """Complexity of the job"""

    disallowed_resources: Optional[List[str]] = FieldInfo(alias="disallowedResources", default=None)
    """List of vehicle names that are allowed to be assigned to this order."""

    duration: Optional[int] = None
    """Service duration of the job"""

    duration_squash: Optional[int] = FieldInfo(alias="durationSquash", default=None)
    """
    Reduced service duration when this job is performed at the same location
    immediately after another job. This optimization recognizes that setup time,
    travel within a building, or equipment preparation may be shared between
    consecutive jobs at the same location. For example, if duration=600 and
    durationSquash=30, the second job at the same location takes only 30 seconds
    instead of 600.
    """

    hard: Optional[bool] = None
    """
    In the case of partialPlanning planning, this indicates whether this order
    should be integrated into the planning or not.
    """

    hard_weight: Optional[int] = FieldInfo(alias="hardWeight", default=None)
    """
    In the case of partialPlanning planning, this indicates the weight of this
    order.
    """

    initial_arrival: Optional[str] = FieldInfo(alias="initialArrival", default=None)
    """Warm start for the arrival time.

    Use this to speed up the solver and to start from an initial solution.
    """

    initial_resource: Optional[str] = FieldInfo(alias="initialResource", default=None)
    """
    Warm start for the assigned resource: name of the vehicle to which this job is
    planned. Use this to speed up the solver and to start from an initial solution.
    """

    job_types: Optional[List[str]] = FieldInfo(alias="jobTypes", default=None)
    """List of job types that this job represents.

    Used to enforce job type limitations per resource per timeframe.
    """

    load: Optional[List[int]] = None
    """Load"""

    location: Optional[Location] = None
    """Geographical Location in WGS-84"""

    padding: Optional[int] = None
    """Padding time before and after the job. In seconds"""

    planned_arrival: Optional[str] = FieldInfo(alias="plannedArrival", default=None)
    """
    Fixed arrival time for this job that creates a soft constraint during
    optimization. The solver will try to schedule the job as close as possible to
    this time, with deviations penalized in the score according to the
    plannedWeight. This allows for customer appointment times or preferred
    scheduling while maintaining optimization flexibility.
    """

    planned_date: Optional[str] = FieldInfo(alias="plannedDate", default=None)
    """Fixed date assignment for this job that must be respected during optimization.

    When specified, the job can only be scheduled on this specific date, creating a
    hard constraint that the solver must honor. Useful for jobs that are already
    committed to customers or have date-specific requirements.
    """

    planned_resource: Optional[str] = FieldInfo(alias="plannedResource", default=None)
    """
    Fixed resource assignment for this job that must be respected during
    optimization. When specified, only the named resource can be assigned to this
    job, creating a hard constraint. Combined with plannedArrival, this allows for
    pre-committed assignments that the solver must work around when optimizing other
    jobs.
    """

    priority: Optional[int] = None
    """Priority level that influences job selection during optimization.

    Higher priority jobs are more likely to be included in the final solution when
    not all jobs can be assigned due to resource or time constraints. The priority
    is multiplied by job duration to calculate the selection weight. Particularly
    important when partialPlanning is enabled. Default value is 1.
    """

    proficiency: Optional[List[Proficiency]] = None
    """List of resource proficiency modifiers for this job.

    Each entry specifies how efficiently a specific resource can complete this job
    by adjusting the effective service duration. Resources with lower
    durationModifier values (e.g., 0.8) complete the job faster, while higher values
    (e.g., 1.5) indicate slower completion.
    """

    rankings: Optional[List[Ranking]] = None
    """List of resource preference rankings for this job.

    Each ranking specifies a resource name and a preference score (1-100), where
    lower values indicate stronger preference. This allows jobs to have preferred
    resources while still allowing assignment to other resources if needed, with the
    preference reflected in the optimization score.
    """

    resumable: Optional[bool] = None
    """Enables job interruption by resource unavailability breaks.

    When true, the job can start before a break, pause during the break, and resume
    afterward. Default: false.
    """

    tags: Optional[List[Tag]] = None
    """List of skill or capability tags that define resource requirements for this job.

    Tags create hard or soft constraints linking jobs to resources with matching
    capabilities. For example, a 'plumbing' tag ensures only resources with plumbing
    skills can be assigned to plumbing jobs.
    """

    urgency: Optional[int] = None
    """Urgency level that influences the scheduling order of jobs.

    Higher urgency jobs are preferentially scheduled earlier in the day and earlier
    in the planning period, helping ensure time-critical tasks are completed first.
    This affects the sequence of job execution rather than job selection.
    """

    windows: Optional[List[Window]] = None
    """List of time windows during which this job can be started or executed.

    Each window defines a start and end time, creating temporal constraints for job
    scheduling. Multiple windows allow for flexible scheduling across different time
    periods. Jobs can only be assigned within these time boundaries.
    """
