# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["ExplanationOptions"]


class ExplanationOptions(BaseModel):
    """Options to manage the explanation of the solution"""

    enabled: Optional[bool] = None
    """
    When enabled the explanation will contain a map of all the alternative positions
    for each job
    """

    filter_hard_constraints: Optional[bool] = FieldInfo(alias="filterHardConstraints", default=None)
    """
    When true the map of alternative positions will contain only feasible
    alternatives
    """

    only_unassigned: Optional[bool] = FieldInfo(alias="onlyUnassigned", default=None)
