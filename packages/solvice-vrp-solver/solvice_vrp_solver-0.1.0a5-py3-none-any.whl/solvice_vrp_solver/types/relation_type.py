# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal, TypeAlias

__all__ = ["RelationType"]

RelationType: TypeAlias = Literal[
    "SAME_TRIP",
    "SEQUENCE",
    "DIRECT_SEQUENCE",
    "SAME_TIME",
    "NEIGHBOR",
    "PICKUP_AND_DELIVERY",
    "SAME_RESOURCE",
    "SAME_DAY",
    "GROUP_SEQUENCE",
]
