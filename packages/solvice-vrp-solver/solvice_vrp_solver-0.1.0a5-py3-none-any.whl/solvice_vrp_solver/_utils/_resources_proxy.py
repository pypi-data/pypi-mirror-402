from __future__ import annotations

from typing import Any
from typing_extensions import override

from ._proxy import LazyProxy


class ResourcesProxy(LazyProxy[Any]):
    """A proxy for the `solvice_vrp_solver.resources` module.

    This is used so that we can lazily import `solvice_vrp_solver.resources` only when
    needed *and* so that users can just import `solvice_vrp_solver` and reference `solvice_vrp_solver.resources`
    """

    @override
    def __load__(self) -> Any:
        import importlib

        mod = importlib.import_module("solvice_vrp_solver.resources")
        return mod


resources = ResourcesProxy().__as_proxied__()
