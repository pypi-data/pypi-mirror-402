# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["Location"]


class Location(BaseModel):
    """Geographical Location in WGS-84"""

    h3_index: Optional[int] = FieldInfo(alias="h3Index", default=None)
    """H3 hexagon index at resolution 9 (optional)"""

    latitude: Optional[float] = None
    """Latitude"""

    longitude: Optional[float] = None
    """Longitude"""
