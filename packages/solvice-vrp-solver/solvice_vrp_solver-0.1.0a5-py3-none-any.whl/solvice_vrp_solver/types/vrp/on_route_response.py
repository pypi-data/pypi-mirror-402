# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .score import Score
from .visit import Visit
from ..._models import BaseModel
from .unresolved import Unresolved
from .onroute_constraint import OnrouteConstraint

__all__ = [
    "OnRouteResponse",
    "Trip",
    "Suggestion",
    "SuggestionAssignment",
    "SuggestionAssignmentScoreExplanation",
    "Violation",
]


class Trip(BaseModel):
    """Trip for a resource. Holds a list of visits for a resource and a date."""

    visits: List[Visit]
    """List of visits for a resource and a date."""

    date: Optional[str] = None
    """Date"""

    departure_time: Optional[str] = FieldInfo(alias="departureTime", default=None)
    """Departure date-time"""

    distance: Optional[int] = None

    end: Optional[Visit] = None
    """Single visit for a resource.

    Holds information of the actual arrival time, the job, the location and the
    latlng.
    """

    occupancy: Optional[float] = None
    """How full this trip is in terms of work time over capacity. Eg 80%"""

    polyline: Optional[str] = None
    """Polyline of the trip"""

    resource: Optional[str] = None
    """Resource"""

    service_time: Optional[int] = FieldInfo(alias="serviceTime", default=None)
    """Service time in seconds"""

    start: Optional[Visit] = None
    """Single visit for a resource.

    Holds information of the actual arrival time, the job, the location and the
    latlng.
    """

    travel_time: Optional[int] = FieldInfo(alias="travelTime", default=None)
    """Travel time in seconds"""

    wait_time: Optional[int] = FieldInfo(alias="waitTime", default=None)
    """Wait time in seconds"""

    work_time: Optional[int] = FieldInfo(alias="workTime", default=None)
    """Work time in seconds"""


class SuggestionAssignmentScoreExplanation(BaseModel):
    """Unresolved constraints in this alternative solution"""

    constraint: OnrouteConstraint
    """Constraint type."""

    score: str
    """Score impact of this conflict."""


class SuggestionAssignment(BaseModel):
    """Assignment for a job to a resource.

    Holds information of the actual arrival time, the job, the resource and the suggested arrival time.
    """

    executed_after: str = FieldInfo(alias="executedAfter")
    """Executed after date-time"""

    job: str
    """Job"""

    resource: str
    """Resource"""

    latest_arrival: Optional[str] = FieldInfo(alias="latestArrival", default=None)
    """Latest arrival date-time"""

    score: Optional[Score] = None
    """
    The score of a solution shows how good this solution is w.r.t all the
    constraints. All solvers try to maximize the score.
    """

    score_explanation: Optional[SuggestionAssignmentScoreExplanation] = FieldInfo(
        alias="scoreExplanation", default=None
    )
    """Unresolved constraints in this alternative solution"""

    suggested_arrival: Optional[str] = FieldInfo(alias="suggestedArrival", default=None)
    """Suggested arrival date-time"""

    suggested_initial_arrival: Optional[datetime] = FieldInfo(alias="suggestedInitialArrival", default=None)

    violations: Optional[List[Unresolved]] = None


class Suggestion(BaseModel):
    assignments: List[SuggestionAssignment]

    score: Score
    """
    The score of a solution shows how good this solution is w.r.t all the
    constraints. All solvers try to maximize the score.
    """


class Violation(BaseModel):
    """
    A constraint that is broken in the current solution with a certain value (penalty) and a certain level (hard, soft, medium).
    """

    level: Optional[Literal["HARD", "SOFT", "MEDIUM"]] = None
    """Level of unresolved constraint."""

    name: Optional[str] = None
    """Name of the constraint."""

    value: Optional[int] = None
    """Value of the unresolved constraint.

    The higher, the more deviation from perfection this constraint has.
    """


class OnRouteResponse(BaseModel):
    """OnRoute response from solve"""

    trips: List[Trip]
    """Actual solution: trips per shift/day and per resource"""

    id: Optional[str] = None
    """Id of the solve job"""

    messages: Optional[List[str]] = None
    """Events and warnings generated during the solver execution"""

    occupancy: Optional[float] = None
    """How full this schedule is in terms of work time (incl travel) over capacity.

    Eg 80%
    """

    score: Optional[Score] = None
    """
    The score of a solution shows how good this solution is w.r.t all the
    constraints. All solvers try to maximize the score.
    """

    status: Optional[Literal["ERROR", "QUEUED", "SOLVING", "SOLVED"]] = None
    """Status of the solve job."""

    suggestions: Optional[List[Suggestion]] = None
    """List of suggested assignments returned by suggest api call"""

    total_service_time_in_seconds: Optional[int] = FieldInfo(alias="totalServiceTimeInSeconds", default=None)
    """Service time for all resources"""

    total_travel_distance_in_meters: Optional[int] = FieldInfo(alias="totalTravelDistanceInMeters", default=None)
    """Travel distance for all resources in meters"""

    total_travel_time_in_seconds: Optional[int] = FieldInfo(alias="totalTravelTimeInSeconds", default=None)
    """Travel time for all resources"""

    total_wait_time_in_seconds: Optional[int] = FieldInfo(alias="totalWaitTimeInSeconds", default=None)
    """Wait time for all resources"""

    unresolved: Optional[object] = None
    """Constraints that are violated"""

    unserved: Optional[List[str]] = None
    """Unserved jobs"""

    unserved_reasons: Optional[Dict[str, object]] = FieldInfo(alias="unservedReasons", default=None)
    """Reasons why jobs could not be served, mapped by job name"""

    violations: Optional[List[Violation]] = None

    workload_fairness: Optional[float] = FieldInfo(alias="workloadFairness", default=None)
