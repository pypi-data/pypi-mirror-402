# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["CustomDistanceMatricesParam"]


class CustomDistanceMatricesParam(TypedDict, total=False):
    """
    Custom distance matrix configuration for multi-profile and multi-slice scenarios
    """

    matrix_service_url: Annotated[Optional[str], PropertyInfo(alias="matrixServiceUrl")]
    """Optional URL for external distance matrix service endpoint.

    If not provided, uses the default system service.
    """

    profile_matrices: Annotated[Optional[Dict[str, Dict[str, str]]], PropertyInfo(alias="profileMatrices")]
    """Map of vehicle profile names (CAR, BIKE, TRUCK) to time slice hour mappings.

    Each time slice hour maps to a matrix ID that should be fetched from the
    distance matrix service. Time slice hours correspond to: 6=MORNING_RUSH,
    9=MORNING, 12=MIDDAY, 14=AFTERNOON, 16=EVENING_RUSH, 20=NIGHT.
    """
