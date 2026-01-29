# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from ..._models import BaseModel
from .onroute_constraint import OnrouteConstraint

__all__ = ["Unresolved"]


class Unresolved(BaseModel):
    """Unresolved constraints in the solution"""

    constraint: OnrouteConstraint
    """Constraint type."""

    score: str
    """Score impact of this conflict."""
