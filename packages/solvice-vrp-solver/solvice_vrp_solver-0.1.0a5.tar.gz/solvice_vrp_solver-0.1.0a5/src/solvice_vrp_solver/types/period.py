# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["Period"]


class Period(BaseModel):
    """Subset of the planning period"""

    end: object
    """End date-time"""

    from_: datetime = FieldInfo(alias="from")
    """Start date-time"""

    to: datetime
