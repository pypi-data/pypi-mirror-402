# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from .job import Job
from .options import Options
from .weights import Weights
from .._models import BaseModel
from .relation import Relation
from .resource import Resource
from .custom_distance_matrices import CustomDistanceMatrices

__all__ = ["Request"]


class Request(BaseModel):
    """OnRoute Request for solving, evaluating"""

    jobs: List[Job]
    """List of jobs/tasks to be assigned to resources.

    Each job specifies service requirements, location, time constraints, duration,
    and resource preferences. Jobs represent the work that needs to be scheduled and
    optimized. At least one job is required, with a maximum of 10,000 jobs per
    request.
    """

    resources: List[Resource]
    """
    List of available resources (vehicles, drivers, workers) that can be assigned to
    perform jobs. Each resource defines their working schedules, location
    constraints, capacity limits, and capabilities. At least one resource is
    required, with a maximum of 2000 resources per request.
    """

    custom_distance_matrices: Optional[CustomDistanceMatrices] = FieldInfo(alias="customDistanceMatrices", default=None)
    """
    Custom distance matrix configuration for multi-profile and multi-slice scenarios
    """

    hook: Optional[str] = None
    """
    Optional webhook URL that will receive a POST request with the job ID when the
    optimization is complete. This enables asynchronous processing where you can
    submit a request and be notified when results are ready, rather than waiting for
    the synchronous response.
    """

    label: Optional[str] = None

    options: Optional[Options] = None
    """Options to tweak the routing engine"""

    relations: Optional[List[Relation]] = None

    weights: Optional[Weights] = None
    """OnRoute Weights"""
