# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["LocationParam"]


class LocationParam(TypedDict, total=False):
    """Geographical Location in WGS-84"""

    h3_index: Annotated[Optional[int], PropertyInfo(alias="h3Index")]
    """H3 hexagon index at resolution 9 (optional)"""

    latitude: float
    """Latitude"""

    longitude: float
    """Longitude"""
