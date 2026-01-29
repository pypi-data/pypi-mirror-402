# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["ExplanationOptionsParam"]


class ExplanationOptionsParam(TypedDict, total=False):
    """Options to manage the explanation of the solution"""

    enabled: Optional[bool]
    """
    When enabled the explanation will contain a map of all the alternative positions
    for each job
    """

    filter_hard_constraints: Annotated[Optional[bool], PropertyInfo(alias="filterHardConstraints")]
    """
    When true the map of alternative positions will contain only feasible
    alternatives
    """

    only_unassigned: Annotated[Optional[bool], PropertyInfo(alias="onlyUnassigned")]
