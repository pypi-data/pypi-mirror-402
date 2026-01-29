# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo
from .relation_type import RelationType

__all__ = ["RelationParam"]


class RelationParam(TypedDict, total=False):
    """Relation between two jobs."""

    jobs: Required[SequenceNotStr[str]]
    """List of job names involved in this relation.

    For sequence-based relations, the order matters - jobs will be executed in the
    order specified. For other relations, order may be irrelevant. All job names
    must exist in the request's jobs list.
    """

    time_interval: Required[Annotated[Literal["FROM_ARRIVAL", "FROM_DEPARTURE"], PropertyInfo(alias="timeInterval")]]
    """Reference point for measuring time intervals between jobs in sequence relations.

    FROM_ARRIVAL (default) measures from when the first job's service begins to when
    the second job's service begins. FROM_DEPARTURE measures from when the first
    job's service ends to when the second job's service begins.
    """

    type: Required[RelationType]
    """Type of relationship constraint between jobs.

    SAME_TRIP: jobs must be on the same vehicle/day. SEQUENCE: jobs must be done in
    order with optional time intervals. DIRECT_SEQUENCE: jobs must be consecutive
    with no other jobs between them. NEIGHBOR: jobs must be geographically close.
    SAME_TIME: jobs must be done simultaneously. PICKUP_AND_DELIVERY: first job is
    pickup, second is delivery. SAME_RESOURCE: jobs must use the same resource.
    SAME_DAY: jobs must be on the same day. GROUP_SEQUENCE: jobs with matching tags
    must be in sequence.
    """

    enforce_compatibility: Annotated[bool, PropertyInfo(alias="enforceCompatibility")]
    """When true, enforces resource compatibility checking for SAME_TIME relations.

    Only compatible resources can work together on linked jobs.
    """

    hard_min_wait: Annotated[bool, PropertyInfo(alias="hardMinWait")]
    """
    When true (default), the minimum time interval constraint is enforced as a hard
    constraint. When false, it becomes a soft constraint that can be violated with
    penalty. Useful for SEQUENCE and SAME_TIME relations where timing flexibility is
    acceptable.
    """

    max_time_interval: Annotated[Optional[int], PropertyInfo(alias="maxTimeInterval")]
    """
    Maximum time interval in seconds allowed between consecutive jobs in sequence
    relations. This prevents excessive delays between related jobs and ensures
    timely completion of job sequences. Only applies to SEQUENCE, DIRECT_SEQUENCE,
    and SAME_TIME relations.
    """

    max_waiting_time: Annotated[Optional[int], PropertyInfo(alias="maxWaitingTime")]
    """Maximum waiting time in seconds between jobs in a SAME_TIME relation.

    This defines how much time synchronization tolerance is allowed - jobs can start
    within this time window of each other. Defaults to 1200 seconds (20 minutes) if
    not specified.
    """

    min_time_interval: Annotated[Optional[int], PropertyInfo(alias="minTimeInterval")]
    """
    Minimum time interval in seconds that must pass between consecutive jobs in
    sequence relations. This ensures adequate time for travel, setup, or processing
    between related jobs. Only applies to SEQUENCE, DIRECT_SEQUENCE, and SAME_TIME
    relations.
    """

    partial_planning: Annotated[bool, PropertyInfo(alias="partialPlanning")]
    """
    Allows the solver to include only some jobs from this relation in the final
    solution when the full relation cannot be satisfied due to constraints. When
    false, either all jobs in the relation are assigned or none are, maintaining the
    relation's integrity.
    """

    resource: Optional[str]
    """Optional resource constraint for this relation.

    When specified, all jobs in the relation must be assigned to this specific
    resource. This creates a hard constraint that can help enforce resource-specific
    workflows or capabilities.
    """

    tags: Optional[SequenceNotStr[str]]
    """List of tag names used to define job groups in GROUP_SEQUENCE relations.

    Jobs with matching tags form groups that must be executed in sequence. This
    allows for complex sequencing rules based on job characteristics rather than
    explicit job names.
    """

    weight: Optional[int]
    """Weight modifier for this relation.

    This can be used to modify the weight of a relation to make it more or less
    important than other relations.
    """
