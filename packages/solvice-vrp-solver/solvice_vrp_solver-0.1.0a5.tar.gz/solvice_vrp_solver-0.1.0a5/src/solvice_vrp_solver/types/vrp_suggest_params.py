# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable, Optional
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo
from .job_param import JobParam
from .options_param import OptionsParam
from .weights_param import WeightsParam
from .relation_param import RelationParam
from .resource_param import ResourceParam
from .custom_distance_matrices_param import CustomDistanceMatricesParam

__all__ = ["VrpSuggestParams"]


class VrpSuggestParams(TypedDict, total=False):
    jobs: Required[Iterable[JobParam]]
    """List of jobs/tasks to be assigned to resources.

    Each job specifies service requirements, location, time constraints, duration,
    and resource preferences. Jobs represent the work that needs to be scheduled and
    optimized. At least one job is required, with a maximum of 10,000 jobs per
    request.
    """

    resources: Required[Iterable[ResourceParam]]
    """
    List of available resources (vehicles, drivers, workers) that can be assigned to
    perform jobs. Each resource defines their working schedules, location
    constraints, capacity limits, and capabilities. At least one resource is
    required, with a maximum of 2000 resources per request.
    """

    millis: Optional[str]

    custom_distance_matrices: Annotated[
        Optional[CustomDistanceMatricesParam], PropertyInfo(alias="customDistanceMatrices")
    ]
    """
    Custom distance matrix configuration for multi-profile and multi-slice scenarios
    """

    hook: Optional[str]
    """
    Optional webhook URL that will receive a POST request with the job ID when the
    optimization is complete. This enables asynchronous processing where you can
    submit a request and be notified when results are ready, rather than waiting for
    the synchronous response.
    """

    label: Optional[str]

    options: Optional[OptionsParam]
    """Options to tweak the routing engine"""

    relations: Optional[Iterable[RelationParam]]

    weights: Optional[WeightsParam]
    """OnRoute Weights"""
