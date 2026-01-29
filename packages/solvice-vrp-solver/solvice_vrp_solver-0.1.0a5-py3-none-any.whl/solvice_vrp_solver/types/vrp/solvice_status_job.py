# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..message import Message
from ..._models import BaseModel

__all__ = ["SolviceStatusJob"]


class SolviceStatusJob(BaseModel):
    """Status of a solve job"""

    id: str
    """Job ID"""

    errors: Optional[List[Message]] = None
    """List of errors"""

    solve_duration: Optional[int] = FieldInfo(alias="solveDuration", default=None)
    """Duration of the solve in seconds"""

    status: Optional[Literal["QUEUED", "SOLVING", "SOLVED", "ERROR"]] = None
    """Status of the solve."""

    warnings: Optional[List[Message]] = None
    """List of warnings"""
