# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["Window"]


class Window(BaseModel):
    """Window in which the job can be executed"""

    from_: str = FieldInfo(alias="from")
    """Date time start of window"""

    to: str
    """Date time end of window"""

    hard: Optional[bool] = None
    """Hard constraint violation of DateWindow"""

    weight: Optional[int] = None
    """Weight constraint modifier"""
