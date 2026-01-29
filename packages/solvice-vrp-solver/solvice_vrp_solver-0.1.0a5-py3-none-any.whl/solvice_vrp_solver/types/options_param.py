# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal, Annotated, TypedDict

from .._utils import PropertyInfo
from .explanation_options_param import ExplanationOptionsParam

__all__ = ["OptionsParam"]


class OptionsParam(TypedDict, total=False):
    """Options to tweak the routing engine"""

    clustering_threshold_meters: Annotated[int, PropertyInfo(alias="clusteringThresholdMeters")]
    """
    Clustering threshold in meters defining the buffer zone around each route's
    bounding box. Routes whose expanded bounding boxes (including buffer) overlap
    will be penalized based on their actual overlap area. This threshold acts as a
    proximity trigger - routes should ideally stay at least this distance apart.
    Default: 10000 meters (10km).
    """

    enable_clustering: Annotated[bool, PropertyInfo(alias="enableClustering")]
    """Enable geographic clustering constraint to discourage route overlap.

    When enabled, routes are penalized if their bounding boxes overlap, encouraging
    visually distinct geographic territories for each route. This is a soft
    constraint that promotes clearer route separation without strictly enforcing
    non-overlapping regions. Default: false.
    """

    euclidian: Optional[bool]
    """
    Use euclidean distance calculations for travel time and distance instead of real
    road networks. When true, straight-line distances are used which is faster but
    less accurate. When false (default), routing engines like OSM, TomTom, or Google
    provide real road distances and travel times.
    """

    explanation: Optional[ExplanationOptionsParam]
    """Options to manage the explanation of the solution"""

    fair_complexity_per_resource: Annotated[Optional[bool], PropertyInfo(alias="fairComplexityPerResource")]

    fair_complexity_per_trip: Annotated[Optional[bool], PropertyInfo(alias="fairComplexityPerTrip")]

    fair_workload_per_resource: Annotated[Optional[bool], PropertyInfo(alias="fairWorkloadPerResource")]
    """Enable workload balancing across different days for each individual resource.

    When true, the solver ensures that each resource's workload is distributed
    evenly across their available days, preventing some days from being overloaded
    while others are underutilized. Works in conjunction with
    `Weights.workloadSpreadWeight` and `options.workloadSensitivity`.
    """

    fair_workload_per_trip: Annotated[Optional[bool], PropertyInfo(alias="fairWorkloadPerTrip")]
    """Enable workload balancing across all resources and all days/trips.

    When true, the solver attempts to distribute service time evenly across all
    resources and time periods, preventing overloading of specific resources or
    days. The effectiveness is controlled by `Weights.workloadSpreadWeight` and
    `options.workloadSensitivity`.
    """

    job_proximity_distance_type: Annotated[
        Optional[Literal["REAL", "HAVERSINE"]], PropertyInfo(alias="jobProximityDistanceType")
    ]
    """The type of distance calculation to use for job proximity calculations"""

    job_proximity_radius: Annotated[Optional[int], PropertyInfo(alias="jobProximityRadius")]
    """Proximity radius in meters for grouping jobs as neighbors.

    Jobs within this distance of each other are considered neighbors for
    proximity-based constraints and optimizations. When set, the solver can leverage
    geographic proximity patterns to optimize routing decisions.
    """

    max_suggestions: Annotated[Optional[int], PropertyInfo(alias="maxSuggestions")]
    """
    Maximum number of alternative assignment suggestions to return when using the
    suggestion endpoint. The solver generates multiple assignment options for
    unassigned jobs, ranked by quality. A value of 0 (default) returns all possible
    suggestions, while values 1-5 limit the results to the best alternatives. Higher
    values increase response time but provide more options.
    """

    minimize_resources: Annotated[Optional[bool], PropertyInfo(alias="minimizeResources")]
    """Primary optimization objective.

    When true, the solver prioritizes using fewer resources (vehicles/drivers) even
    if it increases total travel time. When false, the solver prioritizes minimizing
    total travel time even if it requires more resources. This fundamentally changes
    the optimization strategy.
    """

    only_feasible_suggestions: Annotated[Optional[bool], PropertyInfo(alias="onlyFeasibleSuggestions")]
    """Filter suggestions based on feasibility.

    When true (default), only suggestions that don't violate hard constraints are
    returned if the initial plan is feasible. If the initial plan is infeasible,
    only suggestions that don't worsen the infeasibility are returned. When false,
    all suggestions are returned regardless of feasibility, which may include
    constraint violations.
    """

    partial_planning: Annotated[Optional[bool], PropertyInfo(alias="partialPlanning")]
    """
    Allow the solver to create solutions where not all jobs are assigned to
    resources. When true (default), the solver will assign as many jobs as possible
    while respecting constraints. When false, the solver will only accept solutions
    where all jobs are assigned, which may result in infeasible solutions.
    """

    polylines: Optional[bool]
    """
    Generate detailed route polylines (encoded route geometries) for each trip
    segment. When true, the response includes polyline data that can be used to draw
    routes on maps. This increases processing time and response size but provides
    visual route information for mapping applications.
    """

    routing_engine: Annotated[
        Optional[Literal["OSM", "TOMTOM", "GOOGLE", "ANYMAP"]], PropertyInfo(alias="routingEngine")
    ]
    """The routing engine to use for distance and travel time calculations"""

    snap_unit: Annotated[Optional[int], PropertyInfo(alias="snapUnit")]
    """Time granularity in seconds for arrival time snapping.

    All calculated arrival times are rounded up to the nearest multiple of this
    value. For example, with snapUnit=300 (5 minutes), an arrival time of 08:32
    becomes 08:35. This helps create more practical schedules by avoiding precise
    timings that are difficult to follow in real operations. The snapping affects
    score calculation during optimization.
    """

    traffic: Optional[float]
    """Global traffic multiplier applied to all travel times.

    A value of 1.1 increases travel times by 10% to account for traffic congestion.
    For real-time traffic data, use TomTom or Google routing engines. This is a
    simple approximation for scenarios where precise traffic data is unavailable.
    """

    workload_sensitivity: Annotated[Optional[float], PropertyInfo(alias="workloadSensitivity")]
