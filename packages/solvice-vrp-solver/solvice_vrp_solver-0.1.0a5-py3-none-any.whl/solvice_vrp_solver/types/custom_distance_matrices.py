# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["CustomDistanceMatrices"]


class CustomDistanceMatrices(BaseModel):
    """
    Custom distance matrix configuration for multi-profile and multi-slice scenarios
    """

    matrix_service_url: Optional[str] = FieldInfo(alias="matrixServiceUrl", default=None)
    """Optional URL for external distance matrix service endpoint.

    If not provided, uses the default system service.
    """

    profile_matrices: Optional[Dict[str, Dict[str, str]]] = FieldInfo(alias="profileMatrices", default=None)
    """Map of vehicle profile names (CAR, BIKE, TRUCK) to time slice hour mappings.

    Each time slice hour maps to a matrix ID that should be fetched from the
    distance matrix service. Time slice hours correspond to: 6=MORNING_RUSH,
    9=MORNING, 12=MIDDAY, 14=AFTERNOON, 16=EVENING_RUSH, 20=NIGHT.
    """
