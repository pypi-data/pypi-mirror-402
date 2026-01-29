# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable, Optional

import httpx

from .jobs import (
    JobsResource,
    AsyncJobsResource,
    JobsResourceWithRawResponse,
    AsyncJobsResourceWithRawResponse,
    JobsResourceWithStreamingResponse,
    AsyncJobsResourceWithStreamingResponse,
)
from ...types import (
    vrp_demo_params,
    vrp_solve_params,
    vrp_suggest_params,
    vrp_evaluate_params,
    vrp_sync_solve_params,
    vrp_sync_suggest_params,
    vrp_sync_evaluate_params,
)
from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, strip_not_given, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.request import Request
from ...types.job_param import JobParam
from ...types.options_param import OptionsParam
from ...types.weights_param import WeightsParam
from ...types.relation_param import RelationParam
from ...types.resource_param import ResourceParam
from ...types.vrp.on_route_response import OnRouteResponse
from ...types.vrp.solvice_status_job import SolviceStatusJob
from ...types.custom_distance_matrices_param import CustomDistanceMatricesParam

__all__ = ["VrpResource", "AsyncVrpResource"]


class VrpResource(SyncAPIResource):
    @cached_property
    def jobs(self) -> JobsResource:
        return JobsResource(self._client)

    @cached_property
    def with_raw_response(self) -> VrpResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/solvice/vrp-solver-sdk-python#accessing-raw-response-data-eg-headers
        """
        return VrpResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> VrpResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/solvice/vrp-solver-sdk-python#with_streaming_response
        """
        return VrpResourceWithStreamingResponse(self)

    def demo(
        self,
        *,
        geolocation: Optional[str] | Omit = omit,
        jobs: Optional[int] | Omit = omit,
        radius: Optional[float] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Request:
        """
        Demo of random generated VRP instance

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/v2/vrp/demo",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "geolocation": geolocation,
                        "jobs": jobs,
                        "radius": radius,
                    },
                    vrp_demo_params.VrpDemoParams,
                ),
            ),
            cast_to=Request,
        )

    def evaluate(
        self,
        *,
        jobs: Iterable[JobParam],
        resources: Iterable[ResourceParam],
        custom_distance_matrices: Optional[CustomDistanceMatricesParam] | Omit = omit,
        hook: Optional[str] | Omit = omit,
        label: Optional[str] | Omit = omit,
        options: Optional[OptionsParam] | Omit = omit,
        relations: Optional[Iterable[RelationParam]] | Omit = omit,
        weights: Optional[WeightsParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SolviceStatusJob:
        """
        Will trigger the evaluation run asynchronously.

        Args:
          jobs: List of jobs/tasks to be assigned to resources. Each job specifies service
              requirements, location, time constraints, duration, and resource preferences.
              Jobs represent the work that needs to be scheduled and optimized. At least one
              job is required, with a maximum of 10,000 jobs per request.

          resources: List of available resources (vehicles, drivers, workers) that can be assigned to
              perform jobs. Each resource defines their working schedules, location
              constraints, capacity limits, and capabilities. At least one resource is
              required, with a maximum of 2000 resources per request.

          custom_distance_matrices: Custom distance matrix configuration for multi-profile and multi-slice scenarios

          hook: Optional webhook URL that will receive a POST request with the job ID when the
              optimization is complete. This enables asynchronous processing where you can
              submit a request and be notified when results are ready, rather than waiting for
              the synchronous response.

          options: Options to tweak the routing engine

          weights: OnRoute Weights

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v2/vrp/evaluate",
            body=maybe_transform(
                {
                    "jobs": jobs,
                    "resources": resources,
                    "custom_distance_matrices": custom_distance_matrices,
                    "hook": hook,
                    "label": label,
                    "options": options,
                    "relations": relations,
                    "weights": weights,
                },
                vrp_evaluate_params.VrpEvaluateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SolviceStatusJob,
        )

    def solve(
        self,
        *,
        jobs: Iterable[JobParam],
        resources: Iterable[ResourceParam],
        millis: Optional[str] | Omit = omit,
        custom_distance_matrices: Optional[CustomDistanceMatricesParam] | Omit = omit,
        hook: Optional[str] | Omit = omit,
        label: Optional[str] | Omit = omit,
        options: Optional[OptionsParam] | Omit = omit,
        relations: Optional[Iterable[RelationParam]] | Omit = omit,
        weights: Optional[WeightsParam] | Omit = omit,
        instance: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SolviceStatusJob:
        """
        Will trigger the solver run asynchronously.

        Args:
          jobs: List of jobs/tasks to be assigned to resources. Each job specifies service
              requirements, location, time constraints, duration, and resource preferences.
              Jobs represent the work that needs to be scheduled and optimized. At least one
              job is required, with a maximum of 10,000 jobs per request.

          resources: List of available resources (vehicles, drivers, workers) that can be assigned to
              perform jobs. Each resource defines their working schedules, location
              constraints, capacity limits, and capabilities. At least one resource is
              required, with a maximum of 2000 resources per request.

          custom_distance_matrices: Custom distance matrix configuration for multi-profile and multi-slice scenarios

          hook: Optional webhook URL that will receive a POST request with the job ID when the
              optimization is complete. This enables asynchronous processing where you can
              submit a request and be notified when results are ready, rather than waiting for
              the synchronous response.

          options: Options to tweak the routing engine

          weights: OnRoute Weights

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"instance": instance}), **(extra_headers or {})}
        return self._post(
            "/v2/vrp/solve",
            body=maybe_transform(
                {
                    "jobs": jobs,
                    "resources": resources,
                    "custom_distance_matrices": custom_distance_matrices,
                    "hook": hook,
                    "label": label,
                    "options": options,
                    "relations": relations,
                    "weights": weights,
                },
                vrp_solve_params.VrpSolveParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"millis": millis}, vrp_solve_params.VrpSolveParams),
            ),
            cast_to=SolviceStatusJob,
        )

    def suggest(
        self,
        *,
        jobs: Iterable[JobParam],
        resources: Iterable[ResourceParam],
        millis: Optional[str] | Omit = omit,
        custom_distance_matrices: Optional[CustomDistanceMatricesParam] | Omit = omit,
        hook: Optional[str] | Omit = omit,
        label: Optional[str] | Omit = omit,
        options: Optional[OptionsParam] | Omit = omit,
        relations: Optional[Iterable[RelationParam]] | Omit = omit,
        weights: Optional[WeightsParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SolviceStatusJob:
        """
        Will return the suggest moves for an unassigned job.

        Args:
          jobs: List of jobs/tasks to be assigned to resources. Each job specifies service
              requirements, location, time constraints, duration, and resource preferences.
              Jobs represent the work that needs to be scheduled and optimized. At least one
              job is required, with a maximum of 10,000 jobs per request.

          resources: List of available resources (vehicles, drivers, workers) that can be assigned to
              perform jobs. Each resource defines their working schedules, location
              constraints, capacity limits, and capabilities. At least one resource is
              required, with a maximum of 2000 resources per request.

          custom_distance_matrices: Custom distance matrix configuration for multi-profile and multi-slice scenarios

          hook: Optional webhook URL that will receive a POST request with the job ID when the
              optimization is complete. This enables asynchronous processing where you can
              submit a request and be notified when results are ready, rather than waiting for
              the synchronous response.

          options: Options to tweak the routing engine

          weights: OnRoute Weights

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v2/vrp/suggest",
            body=maybe_transform(
                {
                    "jobs": jobs,
                    "resources": resources,
                    "custom_distance_matrices": custom_distance_matrices,
                    "hook": hook,
                    "label": label,
                    "options": options,
                    "relations": relations,
                    "weights": weights,
                },
                vrp_suggest_params.VrpSuggestParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"millis": millis}, vrp_suggest_params.VrpSuggestParams),
            ),
            cast_to=SolviceStatusJob,
        )

    def sync_evaluate(
        self,
        *,
        jobs: Iterable[JobParam],
        resources: Iterable[ResourceParam],
        custom_distance_matrices: Optional[CustomDistanceMatricesParam] | Omit = omit,
        hook: Optional[str] | Omit = omit,
        label: Optional[str] | Omit = omit,
        options: Optional[OptionsParam] | Omit = omit,
        relations: Optional[Iterable[RelationParam]] | Omit = omit,
        weights: Optional[WeightsParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OnRouteResponse:
        """
        Synchronous evaluate operation for low latency results

        Args:
          jobs: List of jobs/tasks to be assigned to resources. Each job specifies service
              requirements, location, time constraints, duration, and resource preferences.
              Jobs represent the work that needs to be scheduled and optimized. At least one
              job is required, with a maximum of 10,000 jobs per request.

          resources: List of available resources (vehicles, drivers, workers) that can be assigned to
              perform jobs. Each resource defines their working schedules, location
              constraints, capacity limits, and capabilities. At least one resource is
              required, with a maximum of 2000 resources per request.

          custom_distance_matrices: Custom distance matrix configuration for multi-profile and multi-slice scenarios

          hook: Optional webhook URL that will receive a POST request with the job ID when the
              optimization is complete. This enables asynchronous processing where you can
              submit a request and be notified when results are ready, rather than waiting for
              the synchronous response.

          options: Options to tweak the routing engine

          weights: OnRoute Weights

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v2/vrp/sync/evaluate",
            body=maybe_transform(
                {
                    "jobs": jobs,
                    "resources": resources,
                    "custom_distance_matrices": custom_distance_matrices,
                    "hook": hook,
                    "label": label,
                    "options": options,
                    "relations": relations,
                    "weights": weights,
                },
                vrp_sync_evaluate_params.VrpSyncEvaluateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OnRouteResponse,
        )

    def sync_solve(
        self,
        *,
        jobs: Iterable[JobParam],
        resources: Iterable[ResourceParam],
        millis: Optional[str] | Omit = omit,
        custom_distance_matrices: Optional[CustomDistanceMatricesParam] | Omit = omit,
        hook: Optional[str] | Omit = omit,
        label: Optional[str] | Omit = omit,
        options: Optional[OptionsParam] | Omit = omit,
        relations: Optional[Iterable[RelationParam]] | Omit = omit,
        weights: Optional[WeightsParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OnRouteResponse:
        """
        Synchronous solve operation for low latency results

        Args:
          jobs: List of jobs/tasks to be assigned to resources. Each job specifies service
              requirements, location, time constraints, duration, and resource preferences.
              Jobs represent the work that needs to be scheduled and optimized. At least one
              job is required, with a maximum of 10,000 jobs per request.

          resources: List of available resources (vehicles, drivers, workers) that can be assigned to
              perform jobs. Each resource defines their working schedules, location
              constraints, capacity limits, and capabilities. At least one resource is
              required, with a maximum of 2000 resources per request.

          custom_distance_matrices: Custom distance matrix configuration for multi-profile and multi-slice scenarios

          hook: Optional webhook URL that will receive a POST request with the job ID when the
              optimization is complete. This enables asynchronous processing where you can
              submit a request and be notified when results are ready, rather than waiting for
              the synchronous response.

          options: Options to tweak the routing engine

          weights: OnRoute Weights

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v2/vrp/sync/solve",
            body=maybe_transform(
                {
                    "jobs": jobs,
                    "resources": resources,
                    "custom_distance_matrices": custom_distance_matrices,
                    "hook": hook,
                    "label": label,
                    "options": options,
                    "relations": relations,
                    "weights": weights,
                },
                vrp_sync_solve_params.VrpSyncSolveParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"millis": millis}, vrp_sync_solve_params.VrpSyncSolveParams),
            ),
            cast_to=OnRouteResponse,
        )

    def sync_suggest(
        self,
        *,
        jobs: Iterable[JobParam],
        resources: Iterable[ResourceParam],
        millis: Optional[str] | Omit = omit,
        custom_distance_matrices: Optional[CustomDistanceMatricesParam] | Omit = omit,
        hook: Optional[str] | Omit = omit,
        label: Optional[str] | Omit = omit,
        options: Optional[OptionsParam] | Omit = omit,
        relations: Optional[Iterable[RelationParam]] | Omit = omit,
        weights: Optional[WeightsParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OnRouteResponse:
        """
        Synchronous suggest operation for low latency results

        Args:
          jobs: List of jobs/tasks to be assigned to resources. Each job specifies service
              requirements, location, time constraints, duration, and resource preferences.
              Jobs represent the work that needs to be scheduled and optimized. At least one
              job is required, with a maximum of 10,000 jobs per request.

          resources: List of available resources (vehicles, drivers, workers) that can be assigned to
              perform jobs. Each resource defines their working schedules, location
              constraints, capacity limits, and capabilities. At least one resource is
              required, with a maximum of 2000 resources per request.

          custom_distance_matrices: Custom distance matrix configuration for multi-profile and multi-slice scenarios

          hook: Optional webhook URL that will receive a POST request with the job ID when the
              optimization is complete. This enables asynchronous processing where you can
              submit a request and be notified when results are ready, rather than waiting for
              the synchronous response.

          options: Options to tweak the routing engine

          weights: OnRoute Weights

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v2/vrp/sync/suggest",
            body=maybe_transform(
                {
                    "jobs": jobs,
                    "resources": resources,
                    "custom_distance_matrices": custom_distance_matrices,
                    "hook": hook,
                    "label": label,
                    "options": options,
                    "relations": relations,
                    "weights": weights,
                },
                vrp_sync_suggest_params.VrpSyncSuggestParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"millis": millis}, vrp_sync_suggest_params.VrpSyncSuggestParams),
            ),
            cast_to=OnRouteResponse,
        )


class AsyncVrpResource(AsyncAPIResource):
    @cached_property
    def jobs(self) -> AsyncJobsResource:
        return AsyncJobsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncVrpResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/solvice/vrp-solver-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncVrpResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncVrpResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/solvice/vrp-solver-sdk-python#with_streaming_response
        """
        return AsyncVrpResourceWithStreamingResponse(self)

    async def demo(
        self,
        *,
        geolocation: Optional[str] | Omit = omit,
        jobs: Optional[int] | Omit = omit,
        radius: Optional[float] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Request:
        """
        Demo of random generated VRP instance

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/v2/vrp/demo",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "geolocation": geolocation,
                        "jobs": jobs,
                        "radius": radius,
                    },
                    vrp_demo_params.VrpDemoParams,
                ),
            ),
            cast_to=Request,
        )

    async def evaluate(
        self,
        *,
        jobs: Iterable[JobParam],
        resources: Iterable[ResourceParam],
        custom_distance_matrices: Optional[CustomDistanceMatricesParam] | Omit = omit,
        hook: Optional[str] | Omit = omit,
        label: Optional[str] | Omit = omit,
        options: Optional[OptionsParam] | Omit = omit,
        relations: Optional[Iterable[RelationParam]] | Omit = omit,
        weights: Optional[WeightsParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SolviceStatusJob:
        """
        Will trigger the evaluation run asynchronously.

        Args:
          jobs: List of jobs/tasks to be assigned to resources. Each job specifies service
              requirements, location, time constraints, duration, and resource preferences.
              Jobs represent the work that needs to be scheduled and optimized. At least one
              job is required, with a maximum of 10,000 jobs per request.

          resources: List of available resources (vehicles, drivers, workers) that can be assigned to
              perform jobs. Each resource defines their working schedules, location
              constraints, capacity limits, and capabilities. At least one resource is
              required, with a maximum of 2000 resources per request.

          custom_distance_matrices: Custom distance matrix configuration for multi-profile and multi-slice scenarios

          hook: Optional webhook URL that will receive a POST request with the job ID when the
              optimization is complete. This enables asynchronous processing where you can
              submit a request and be notified when results are ready, rather than waiting for
              the synchronous response.

          options: Options to tweak the routing engine

          weights: OnRoute Weights

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v2/vrp/evaluate",
            body=await async_maybe_transform(
                {
                    "jobs": jobs,
                    "resources": resources,
                    "custom_distance_matrices": custom_distance_matrices,
                    "hook": hook,
                    "label": label,
                    "options": options,
                    "relations": relations,
                    "weights": weights,
                },
                vrp_evaluate_params.VrpEvaluateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SolviceStatusJob,
        )

    async def solve(
        self,
        *,
        jobs: Iterable[JobParam],
        resources: Iterable[ResourceParam],
        millis: Optional[str] | Omit = omit,
        custom_distance_matrices: Optional[CustomDistanceMatricesParam] | Omit = omit,
        hook: Optional[str] | Omit = omit,
        label: Optional[str] | Omit = omit,
        options: Optional[OptionsParam] | Omit = omit,
        relations: Optional[Iterable[RelationParam]] | Omit = omit,
        weights: Optional[WeightsParam] | Omit = omit,
        instance: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SolviceStatusJob:
        """
        Will trigger the solver run asynchronously.

        Args:
          jobs: List of jobs/tasks to be assigned to resources. Each job specifies service
              requirements, location, time constraints, duration, and resource preferences.
              Jobs represent the work that needs to be scheduled and optimized. At least one
              job is required, with a maximum of 10,000 jobs per request.

          resources: List of available resources (vehicles, drivers, workers) that can be assigned to
              perform jobs. Each resource defines their working schedules, location
              constraints, capacity limits, and capabilities. At least one resource is
              required, with a maximum of 2000 resources per request.

          custom_distance_matrices: Custom distance matrix configuration for multi-profile and multi-slice scenarios

          hook: Optional webhook URL that will receive a POST request with the job ID when the
              optimization is complete. This enables asynchronous processing where you can
              submit a request and be notified when results are ready, rather than waiting for
              the synchronous response.

          options: Options to tweak the routing engine

          weights: OnRoute Weights

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"instance": instance}), **(extra_headers or {})}
        return await self._post(
            "/v2/vrp/solve",
            body=await async_maybe_transform(
                {
                    "jobs": jobs,
                    "resources": resources,
                    "custom_distance_matrices": custom_distance_matrices,
                    "hook": hook,
                    "label": label,
                    "options": options,
                    "relations": relations,
                    "weights": weights,
                },
                vrp_solve_params.VrpSolveParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform({"millis": millis}, vrp_solve_params.VrpSolveParams),
            ),
            cast_to=SolviceStatusJob,
        )

    async def suggest(
        self,
        *,
        jobs: Iterable[JobParam],
        resources: Iterable[ResourceParam],
        millis: Optional[str] | Omit = omit,
        custom_distance_matrices: Optional[CustomDistanceMatricesParam] | Omit = omit,
        hook: Optional[str] | Omit = omit,
        label: Optional[str] | Omit = omit,
        options: Optional[OptionsParam] | Omit = omit,
        relations: Optional[Iterable[RelationParam]] | Omit = omit,
        weights: Optional[WeightsParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SolviceStatusJob:
        """
        Will return the suggest moves for an unassigned job.

        Args:
          jobs: List of jobs/tasks to be assigned to resources. Each job specifies service
              requirements, location, time constraints, duration, and resource preferences.
              Jobs represent the work that needs to be scheduled and optimized. At least one
              job is required, with a maximum of 10,000 jobs per request.

          resources: List of available resources (vehicles, drivers, workers) that can be assigned to
              perform jobs. Each resource defines their working schedules, location
              constraints, capacity limits, and capabilities. At least one resource is
              required, with a maximum of 2000 resources per request.

          custom_distance_matrices: Custom distance matrix configuration for multi-profile and multi-slice scenarios

          hook: Optional webhook URL that will receive a POST request with the job ID when the
              optimization is complete. This enables asynchronous processing where you can
              submit a request and be notified when results are ready, rather than waiting for
              the synchronous response.

          options: Options to tweak the routing engine

          weights: OnRoute Weights

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v2/vrp/suggest",
            body=await async_maybe_transform(
                {
                    "jobs": jobs,
                    "resources": resources,
                    "custom_distance_matrices": custom_distance_matrices,
                    "hook": hook,
                    "label": label,
                    "options": options,
                    "relations": relations,
                    "weights": weights,
                },
                vrp_suggest_params.VrpSuggestParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform({"millis": millis}, vrp_suggest_params.VrpSuggestParams),
            ),
            cast_to=SolviceStatusJob,
        )

    async def sync_evaluate(
        self,
        *,
        jobs: Iterable[JobParam],
        resources: Iterable[ResourceParam],
        custom_distance_matrices: Optional[CustomDistanceMatricesParam] | Omit = omit,
        hook: Optional[str] | Omit = omit,
        label: Optional[str] | Omit = omit,
        options: Optional[OptionsParam] | Omit = omit,
        relations: Optional[Iterable[RelationParam]] | Omit = omit,
        weights: Optional[WeightsParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OnRouteResponse:
        """
        Synchronous evaluate operation for low latency results

        Args:
          jobs: List of jobs/tasks to be assigned to resources. Each job specifies service
              requirements, location, time constraints, duration, and resource preferences.
              Jobs represent the work that needs to be scheduled and optimized. At least one
              job is required, with a maximum of 10,000 jobs per request.

          resources: List of available resources (vehicles, drivers, workers) that can be assigned to
              perform jobs. Each resource defines their working schedules, location
              constraints, capacity limits, and capabilities. At least one resource is
              required, with a maximum of 2000 resources per request.

          custom_distance_matrices: Custom distance matrix configuration for multi-profile and multi-slice scenarios

          hook: Optional webhook URL that will receive a POST request with the job ID when the
              optimization is complete. This enables asynchronous processing where you can
              submit a request and be notified when results are ready, rather than waiting for
              the synchronous response.

          options: Options to tweak the routing engine

          weights: OnRoute Weights

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v2/vrp/sync/evaluate",
            body=await async_maybe_transform(
                {
                    "jobs": jobs,
                    "resources": resources,
                    "custom_distance_matrices": custom_distance_matrices,
                    "hook": hook,
                    "label": label,
                    "options": options,
                    "relations": relations,
                    "weights": weights,
                },
                vrp_sync_evaluate_params.VrpSyncEvaluateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OnRouteResponse,
        )

    async def sync_solve(
        self,
        *,
        jobs: Iterable[JobParam],
        resources: Iterable[ResourceParam],
        millis: Optional[str] | Omit = omit,
        custom_distance_matrices: Optional[CustomDistanceMatricesParam] | Omit = omit,
        hook: Optional[str] | Omit = omit,
        label: Optional[str] | Omit = omit,
        options: Optional[OptionsParam] | Omit = omit,
        relations: Optional[Iterable[RelationParam]] | Omit = omit,
        weights: Optional[WeightsParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OnRouteResponse:
        """
        Synchronous solve operation for low latency results

        Args:
          jobs: List of jobs/tasks to be assigned to resources. Each job specifies service
              requirements, location, time constraints, duration, and resource preferences.
              Jobs represent the work that needs to be scheduled and optimized. At least one
              job is required, with a maximum of 10,000 jobs per request.

          resources: List of available resources (vehicles, drivers, workers) that can be assigned to
              perform jobs. Each resource defines their working schedules, location
              constraints, capacity limits, and capabilities. At least one resource is
              required, with a maximum of 2000 resources per request.

          custom_distance_matrices: Custom distance matrix configuration for multi-profile and multi-slice scenarios

          hook: Optional webhook URL that will receive a POST request with the job ID when the
              optimization is complete. This enables asynchronous processing where you can
              submit a request and be notified when results are ready, rather than waiting for
              the synchronous response.

          options: Options to tweak the routing engine

          weights: OnRoute Weights

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v2/vrp/sync/solve",
            body=await async_maybe_transform(
                {
                    "jobs": jobs,
                    "resources": resources,
                    "custom_distance_matrices": custom_distance_matrices,
                    "hook": hook,
                    "label": label,
                    "options": options,
                    "relations": relations,
                    "weights": weights,
                },
                vrp_sync_solve_params.VrpSyncSolveParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform({"millis": millis}, vrp_sync_solve_params.VrpSyncSolveParams),
            ),
            cast_to=OnRouteResponse,
        )

    async def sync_suggest(
        self,
        *,
        jobs: Iterable[JobParam],
        resources: Iterable[ResourceParam],
        millis: Optional[str] | Omit = omit,
        custom_distance_matrices: Optional[CustomDistanceMatricesParam] | Omit = omit,
        hook: Optional[str] | Omit = omit,
        label: Optional[str] | Omit = omit,
        options: Optional[OptionsParam] | Omit = omit,
        relations: Optional[Iterable[RelationParam]] | Omit = omit,
        weights: Optional[WeightsParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OnRouteResponse:
        """
        Synchronous suggest operation for low latency results

        Args:
          jobs: List of jobs/tasks to be assigned to resources. Each job specifies service
              requirements, location, time constraints, duration, and resource preferences.
              Jobs represent the work that needs to be scheduled and optimized. At least one
              job is required, with a maximum of 10,000 jobs per request.

          resources: List of available resources (vehicles, drivers, workers) that can be assigned to
              perform jobs. Each resource defines their working schedules, location
              constraints, capacity limits, and capabilities. At least one resource is
              required, with a maximum of 2000 resources per request.

          custom_distance_matrices: Custom distance matrix configuration for multi-profile and multi-slice scenarios

          hook: Optional webhook URL that will receive a POST request with the job ID when the
              optimization is complete. This enables asynchronous processing where you can
              submit a request and be notified when results are ready, rather than waiting for
              the synchronous response.

          options: Options to tweak the routing engine

          weights: OnRoute Weights

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v2/vrp/sync/suggest",
            body=await async_maybe_transform(
                {
                    "jobs": jobs,
                    "resources": resources,
                    "custom_distance_matrices": custom_distance_matrices,
                    "hook": hook,
                    "label": label,
                    "options": options,
                    "relations": relations,
                    "weights": weights,
                },
                vrp_sync_suggest_params.VrpSyncSuggestParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform({"millis": millis}, vrp_sync_suggest_params.VrpSyncSuggestParams),
            ),
            cast_to=OnRouteResponse,
        )


class VrpResourceWithRawResponse:
    def __init__(self, vrp: VrpResource) -> None:
        self._vrp = vrp

        self.demo = to_raw_response_wrapper(
            vrp.demo,
        )
        self.evaluate = to_raw_response_wrapper(
            vrp.evaluate,
        )
        self.solve = to_raw_response_wrapper(
            vrp.solve,
        )
        self.suggest = to_raw_response_wrapper(
            vrp.suggest,
        )
        self.sync_evaluate = to_raw_response_wrapper(
            vrp.sync_evaluate,
        )
        self.sync_solve = to_raw_response_wrapper(
            vrp.sync_solve,
        )
        self.sync_suggest = to_raw_response_wrapper(
            vrp.sync_suggest,
        )

    @cached_property
    def jobs(self) -> JobsResourceWithRawResponse:
        return JobsResourceWithRawResponse(self._vrp.jobs)


class AsyncVrpResourceWithRawResponse:
    def __init__(self, vrp: AsyncVrpResource) -> None:
        self._vrp = vrp

        self.demo = async_to_raw_response_wrapper(
            vrp.demo,
        )
        self.evaluate = async_to_raw_response_wrapper(
            vrp.evaluate,
        )
        self.solve = async_to_raw_response_wrapper(
            vrp.solve,
        )
        self.suggest = async_to_raw_response_wrapper(
            vrp.suggest,
        )
        self.sync_evaluate = async_to_raw_response_wrapper(
            vrp.sync_evaluate,
        )
        self.sync_solve = async_to_raw_response_wrapper(
            vrp.sync_solve,
        )
        self.sync_suggest = async_to_raw_response_wrapper(
            vrp.sync_suggest,
        )

    @cached_property
    def jobs(self) -> AsyncJobsResourceWithRawResponse:
        return AsyncJobsResourceWithRawResponse(self._vrp.jobs)


class VrpResourceWithStreamingResponse:
    def __init__(self, vrp: VrpResource) -> None:
        self._vrp = vrp

        self.demo = to_streamed_response_wrapper(
            vrp.demo,
        )
        self.evaluate = to_streamed_response_wrapper(
            vrp.evaluate,
        )
        self.solve = to_streamed_response_wrapper(
            vrp.solve,
        )
        self.suggest = to_streamed_response_wrapper(
            vrp.suggest,
        )
        self.sync_evaluate = to_streamed_response_wrapper(
            vrp.sync_evaluate,
        )
        self.sync_solve = to_streamed_response_wrapper(
            vrp.sync_solve,
        )
        self.sync_suggest = to_streamed_response_wrapper(
            vrp.sync_suggest,
        )

    @cached_property
    def jobs(self) -> JobsResourceWithStreamingResponse:
        return JobsResourceWithStreamingResponse(self._vrp.jobs)


class AsyncVrpResourceWithStreamingResponse:
    def __init__(self, vrp: AsyncVrpResource) -> None:
        self._vrp = vrp

        self.demo = async_to_streamed_response_wrapper(
            vrp.demo,
        )
        self.evaluate = async_to_streamed_response_wrapper(
            vrp.evaluate,
        )
        self.solve = async_to_streamed_response_wrapper(
            vrp.solve,
        )
        self.suggest = async_to_streamed_response_wrapper(
            vrp.suggest,
        )
        self.sync_evaluate = async_to_streamed_response_wrapper(
            vrp.sync_evaluate,
        )
        self.sync_solve = async_to_streamed_response_wrapper(
            vrp.sync_solve,
        )
        self.sync_suggest = async_to_streamed_response_wrapper(
            vrp.sync_suggest,
        )

    @cached_property
    def jobs(self) -> AsyncJobsResourceWithStreamingResponse:
        return AsyncJobsResourceWithStreamingResponse(self._vrp.jobs)
