# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["Score"]


class Score(BaseModel):
    """
    The score of a solution shows how good this solution is w.r.t all the constraints. All solvers try to maximize the score.
    """

    feasible: Optional[bool] = None

    hard_score: Optional[int] = FieldInfo(alias="hardScore", default=None)
    """The score of the constraints that are hard.

    This should be 0 in order to be feasible.
    """

    medium_score: Optional[int] = FieldInfo(alias="mediumScore", default=None)
    """The score of the constraints that are medium."""

    soft_score: Optional[int] = FieldInfo(alias="softScore", default=None)
    """The score of the constraints that are soft."""
