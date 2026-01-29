# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from solvice_vrp_solver import SolviceVrpSolver, AsyncSolviceVrpSolver
from solvice_vrp_solver.types import (
    Request,
)
from solvice_vrp_solver._utils import parse_datetime
from solvice_vrp_solver.types.vrp import OnRouteResponse, SolviceStatusJob

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestVrp:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_demo(self, client: SolviceVrpSolver) -> None:
        vrp = client.vrp.demo()
        assert_matches_type(Request, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_demo_with_all_params(self, client: SolviceVrpSolver) -> None:
        vrp = client.vrp.demo(
            geolocation="geolocation",
            jobs=0,
            radius=0,
        )
        assert_matches_type(Request, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_demo(self, client: SolviceVrpSolver) -> None:
        response = client.vrp.with_raw_response.demo()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        vrp = response.parse()
        assert_matches_type(Request, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_demo(self, client: SolviceVrpSolver) -> None:
        with client.vrp.with_streaming_response.demo() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            vrp = response.parse()
            assert_matches_type(Request, vrp, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_evaluate(self, client: SolviceVrpSolver) -> None:
        vrp = client.vrp.evaluate(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        )
        assert_matches_type(SolviceStatusJob, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_evaluate_with_all_params(self, client: SolviceVrpSolver) -> None:
        vrp = client.vrp.evaluate(
            jobs=[
                {
                    "name": "Job-1",
                    "allowed_resources": ["string"],
                    "complexity": 1,
                    "disallowed_resources": ["vehicle-3", "vehicle-4"],
                    "duration": 600,
                    "duration_squash": 30,
                    "hard": True,
                    "hard_weight": 1,
                    "initial_arrival": "2023-01-13T09:00:00Z",
                    "initial_resource": "vehicle-1",
                    "job_types": ["Initial Appointment", "Wound Care"],
                    "load": [5, 10],
                    "location": {
                        "h3_index": 617700169958293500,
                        "latitude": 51.0543,
                        "longitude": 3.7174,
                    },
                    "padding": 300,
                    "planned_arrival": "2023-01-13T09:00:00Z",
                    "planned_date": "2023-01-13",
                    "planned_resource": "vehicle-1",
                    "priority": 100,
                    "proficiency": [
                        {
                            "resource": "senior-technician",
                            "duration_modifier": 0.8,
                        }
                    ],
                    "rankings": [
                        {
                            "name": "certified-technician",
                            "ranking": 5,
                        }
                    ],
                    "resumable": True,
                    "tags": [
                        {
                            "name": "plumbing",
                            "hard": False,
                            "weight": 300,
                        }
                    ],
                    "urgency": 80,
                    "windows": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T12:00:00Z",
                            "hard": True,
                            "weight": 1,
                        }
                    ],
                }
            ],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                            "breaks": [{"type": "WINDOWED"}],
                            "end": {
                                "h3_index": 617700169958293500,
                                "latitude": 51.0543,
                                "longitude": 3.7174,
                            },
                            "ignore_travel_time_from_last_job": False,
                            "ignore_travel_time_to_first_job": False,
                            "job_type_limitations": {
                                "Initial Appointment": 2,
                                "Wound Care": 1,
                            },
                            "overtime": {},
                            "overtime_end": "2023-01-13T19:00:00Z",
                            "start": {
                                "h3_index": 617700169958293500,
                                "latitude": 51.0543,
                                "longitude": 3.7174,
                            },
                            "tags": ["delivery", "installation"],
                        }
                    ],
                    "capacity": [500, 200],
                    "category": "CAR",
                    "compatible_resources": ["driver2", "driver3"],
                    "end": {
                        "h3_index": 617700169958293500,
                        "latitude": 50.0987624,
                        "longitude": 4.93849204,
                    },
                    "hourly_cost": 25,
                    "max_drive_distance": 0,
                    "max_drive_time": 0,
                    "max_drive_time_in_seconds": 28800,
                    "max_drive_time_job": 7200,
                    "region": {
                        "h3_index": 617700169958293500,
                        "latitude": 51.05,
                        "longitude": 3.72,
                    },
                    "rules": [
                        {
                            "job_type_limitations": {
                                "Initial Appointment": 10,
                                "Wound Care": 5,
                            },
                            "max_drive_time": 10800,
                            "max_job_complexity": 0,
                            "max_service_time": 21600,
                            "max_work_time": 28800,
                            "min_drive_time": 3600,
                            "min_job_complexity": 0,
                            "min_service_time": 7200,
                            "min_work_time": 14400,
                            "period": {
                                "end": "2007-12-31T17:00:00",
                                "from": parse_datetime("2024-01-01T08:00:00Z"),
                                "to": parse_datetime("2024-01-07T17:00:00Z"),
                            },
                        }
                    ],
                    "start": {
                        "h3_index": 617700169958293500,
                        "latitude": 50.0987624,
                        "longitude": 4.93849204,
                    },
                    "tags": ["plumbing", "electrical"],
                }
            ],
            custom_distance_matrices={
                "matrix_service_url": "https://custom-matrix-service.com/api",
                "profile_matrices": {
                    "CAR": {
                        "6": "matrix-car-morning-123",
                        "9": "matrix-car-midday-456",
                        "16": "matrix-car-evening-789",
                    },
                    "TRUCK": {
                        "6": "matrix-truck-morning-abc",
                        "9": "matrix-truck-midday-def",
                    },
                },
            },
            hook="https://example.com",
            label="label",
            options={
                "clustering_threshold_meters": 10000,
                "enable_clustering": False,
                "euclidian": False,
                "explanation": {
                    "enabled": True,
                    "filter_hard_constraints": True,
                    "only_unassigned": True,
                },
                "fair_complexity_per_resource": True,
                "fair_complexity_per_trip": True,
                "fair_workload_per_resource": False,
                "fair_workload_per_trip": False,
                "job_proximity_distance_type": "HAVERSINE",
                "job_proximity_radius": 5000,
                "max_suggestions": 3,
                "minimize_resources": True,
                "only_feasible_suggestions": True,
                "partial_planning": True,
                "polylines": True,
                "routing_engine": "OSM",
                "snap_unit": 300,
                "traffic": 1.1,
                "workload_sensitivity": 0.1,
            },
            relations=[
                {
                    "jobs": ["Job-1", "Job-2"],
                    "time_interval": "FROM_ARRIVAL",
                    "type": "SEQUENCE",
                    "enforce_compatibility": True,
                    "hard_min_wait": True,
                    "max_time_interval": 3600,
                    "max_waiting_time": 1200,
                    "min_time_interval": 0,
                    "partial_planning": False,
                    "resource": "vehicle-1",
                    "tags": ["urgent"],
                    "weight": 1,
                }
            ],
            weights={
                "allowed_resources_weight": 500,
                "asap_weight": 5,
                "clustering_weight": 1,
                "drive_time_weight": 1,
                "job_proximity_weight": 1000,
                "minimize_resources_weight": 0,
                "planned_weight": 1000,
                "priority_weight": 100,
                "ranking_weight": 10,
                "travel_time_weight": 1,
                "urgency_weight": 50,
                "wait_time_weight": 1,
                "workload_spread_weight": 10,
            },
        )
        assert_matches_type(SolviceStatusJob, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_evaluate(self, client: SolviceVrpSolver) -> None:
        response = client.vrp.with_raw_response.evaluate(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        vrp = response.parse()
        assert_matches_type(SolviceStatusJob, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_evaluate(self, client: SolviceVrpSolver) -> None:
        with client.vrp.with_streaming_response.evaluate(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            vrp = response.parse()
            assert_matches_type(SolviceStatusJob, vrp, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_solve(self, client: SolviceVrpSolver) -> None:
        vrp = client.vrp.solve(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        )
        assert_matches_type(SolviceStatusJob, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_solve_with_all_params(self, client: SolviceVrpSolver) -> None:
        vrp = client.vrp.solve(
            jobs=[
                {
                    "name": "Job-1",
                    "allowed_resources": ["string"],
                    "complexity": 1,
                    "disallowed_resources": ["vehicle-3", "vehicle-4"],
                    "duration": 600,
                    "duration_squash": 30,
                    "hard": True,
                    "hard_weight": 1,
                    "initial_arrival": "2023-01-13T09:00:00Z",
                    "initial_resource": "vehicle-1",
                    "job_types": ["Initial Appointment", "Wound Care"],
                    "load": [5, 10],
                    "location": {
                        "h3_index": 617700169958293500,
                        "latitude": 51.0543,
                        "longitude": 3.7174,
                    },
                    "padding": 300,
                    "planned_arrival": "2023-01-13T09:00:00Z",
                    "planned_date": "2023-01-13",
                    "planned_resource": "vehicle-1",
                    "priority": 100,
                    "proficiency": [
                        {
                            "resource": "senior-technician",
                            "duration_modifier": 0.8,
                        }
                    ],
                    "rankings": [
                        {
                            "name": "certified-technician",
                            "ranking": 5,
                        }
                    ],
                    "resumable": True,
                    "tags": [
                        {
                            "name": "plumbing",
                            "hard": False,
                            "weight": 300,
                        }
                    ],
                    "urgency": 80,
                    "windows": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T12:00:00Z",
                            "hard": True,
                            "weight": 1,
                        }
                    ],
                }
            ],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                            "breaks": [{"type": "WINDOWED"}],
                            "end": {
                                "h3_index": 617700169958293500,
                                "latitude": 51.0543,
                                "longitude": 3.7174,
                            },
                            "ignore_travel_time_from_last_job": False,
                            "ignore_travel_time_to_first_job": False,
                            "job_type_limitations": {
                                "Initial Appointment": 2,
                                "Wound Care": 1,
                            },
                            "overtime": {},
                            "overtime_end": "2023-01-13T19:00:00Z",
                            "start": {
                                "h3_index": 617700169958293500,
                                "latitude": 51.0543,
                                "longitude": 3.7174,
                            },
                            "tags": ["delivery", "installation"],
                        }
                    ],
                    "capacity": [500, 200],
                    "category": "CAR",
                    "compatible_resources": ["driver2", "driver3"],
                    "end": {
                        "h3_index": 617700169958293500,
                        "latitude": 50.0987624,
                        "longitude": 4.93849204,
                    },
                    "hourly_cost": 25,
                    "max_drive_distance": 0,
                    "max_drive_time": 0,
                    "max_drive_time_in_seconds": 28800,
                    "max_drive_time_job": 7200,
                    "region": {
                        "h3_index": 617700169958293500,
                        "latitude": 51.05,
                        "longitude": 3.72,
                    },
                    "rules": [
                        {
                            "job_type_limitations": {
                                "Initial Appointment": 10,
                                "Wound Care": 5,
                            },
                            "max_drive_time": 10800,
                            "max_job_complexity": 0,
                            "max_service_time": 21600,
                            "max_work_time": 28800,
                            "min_drive_time": 3600,
                            "min_job_complexity": 0,
                            "min_service_time": 7200,
                            "min_work_time": 14400,
                            "period": {
                                "end": "2007-12-31T17:00:00",
                                "from": parse_datetime("2024-01-01T08:00:00Z"),
                                "to": parse_datetime("2024-01-07T17:00:00Z"),
                            },
                        }
                    ],
                    "start": {
                        "h3_index": 617700169958293500,
                        "latitude": 50.0987624,
                        "longitude": 4.93849204,
                    },
                    "tags": ["plumbing", "electrical"],
                }
            ],
            millis="millis",
            custom_distance_matrices={
                "matrix_service_url": "https://custom-matrix-service.com/api",
                "profile_matrices": {
                    "CAR": {
                        "6": "matrix-car-morning-123",
                        "9": "matrix-car-midday-456",
                        "16": "matrix-car-evening-789",
                    },
                    "TRUCK": {
                        "6": "matrix-truck-morning-abc",
                        "9": "matrix-truck-midday-def",
                    },
                },
            },
            hook="https://example.com",
            label="label",
            options={
                "clustering_threshold_meters": 10000,
                "enable_clustering": False,
                "euclidian": False,
                "explanation": {
                    "enabled": True,
                    "filter_hard_constraints": True,
                    "only_unassigned": True,
                },
                "fair_complexity_per_resource": True,
                "fair_complexity_per_trip": True,
                "fair_workload_per_resource": False,
                "fair_workload_per_trip": False,
                "job_proximity_distance_type": "HAVERSINE",
                "job_proximity_radius": 5000,
                "max_suggestions": 3,
                "minimize_resources": True,
                "only_feasible_suggestions": True,
                "partial_planning": True,
                "polylines": True,
                "routing_engine": "OSM",
                "snap_unit": 300,
                "traffic": 1.1,
                "workload_sensitivity": 0.1,
            },
            relations=[
                {
                    "jobs": ["Job-1", "Job-2"],
                    "time_interval": "FROM_ARRIVAL",
                    "type": "SEQUENCE",
                    "enforce_compatibility": True,
                    "hard_min_wait": True,
                    "max_time_interval": 3600,
                    "max_waiting_time": 1200,
                    "min_time_interval": 0,
                    "partial_planning": False,
                    "resource": "vehicle-1",
                    "tags": ["urgent"],
                    "weight": 1,
                }
            ],
            weights={
                "allowed_resources_weight": 500,
                "asap_weight": 5,
                "clustering_weight": 1,
                "drive_time_weight": 1,
                "job_proximity_weight": 1000,
                "minimize_resources_weight": 0,
                "planned_weight": 1000,
                "priority_weight": 100,
                "ranking_weight": 10,
                "travel_time_weight": 1,
                "urgency_weight": 50,
                "wait_time_weight": 1,
                "workload_spread_weight": 10,
            },
            instance="instance",
        )
        assert_matches_type(SolviceStatusJob, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_solve(self, client: SolviceVrpSolver) -> None:
        response = client.vrp.with_raw_response.solve(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        vrp = response.parse()
        assert_matches_type(SolviceStatusJob, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_solve(self, client: SolviceVrpSolver) -> None:
        with client.vrp.with_streaming_response.solve(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            vrp = response.parse()
            assert_matches_type(SolviceStatusJob, vrp, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_suggest(self, client: SolviceVrpSolver) -> None:
        vrp = client.vrp.suggest(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        )
        assert_matches_type(SolviceStatusJob, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_suggest_with_all_params(self, client: SolviceVrpSolver) -> None:
        vrp = client.vrp.suggest(
            jobs=[
                {
                    "name": "Job-1",
                    "allowed_resources": ["string"],
                    "complexity": 1,
                    "disallowed_resources": ["vehicle-3", "vehicle-4"],
                    "duration": 600,
                    "duration_squash": 30,
                    "hard": True,
                    "hard_weight": 1,
                    "initial_arrival": "2023-01-13T09:00:00Z",
                    "initial_resource": "vehicle-1",
                    "job_types": ["Initial Appointment", "Wound Care"],
                    "load": [5, 10],
                    "location": {
                        "h3_index": 617700169958293500,
                        "latitude": 51.0543,
                        "longitude": 3.7174,
                    },
                    "padding": 300,
                    "planned_arrival": "2023-01-13T09:00:00Z",
                    "planned_date": "2023-01-13",
                    "planned_resource": "vehicle-1",
                    "priority": 100,
                    "proficiency": [
                        {
                            "resource": "senior-technician",
                            "duration_modifier": 0.8,
                        }
                    ],
                    "rankings": [
                        {
                            "name": "certified-technician",
                            "ranking": 5,
                        }
                    ],
                    "resumable": True,
                    "tags": [
                        {
                            "name": "plumbing",
                            "hard": False,
                            "weight": 300,
                        }
                    ],
                    "urgency": 80,
                    "windows": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T12:00:00Z",
                            "hard": True,
                            "weight": 1,
                        }
                    ],
                }
            ],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                            "breaks": [{"type": "WINDOWED"}],
                            "end": {
                                "h3_index": 617700169958293500,
                                "latitude": 51.0543,
                                "longitude": 3.7174,
                            },
                            "ignore_travel_time_from_last_job": False,
                            "ignore_travel_time_to_first_job": False,
                            "job_type_limitations": {
                                "Initial Appointment": 2,
                                "Wound Care": 1,
                            },
                            "overtime": {},
                            "overtime_end": "2023-01-13T19:00:00Z",
                            "start": {
                                "h3_index": 617700169958293500,
                                "latitude": 51.0543,
                                "longitude": 3.7174,
                            },
                            "tags": ["delivery", "installation"],
                        }
                    ],
                    "capacity": [500, 200],
                    "category": "CAR",
                    "compatible_resources": ["driver2", "driver3"],
                    "end": {
                        "h3_index": 617700169958293500,
                        "latitude": 50.0987624,
                        "longitude": 4.93849204,
                    },
                    "hourly_cost": 25,
                    "max_drive_distance": 0,
                    "max_drive_time": 0,
                    "max_drive_time_in_seconds": 28800,
                    "max_drive_time_job": 7200,
                    "region": {
                        "h3_index": 617700169958293500,
                        "latitude": 51.05,
                        "longitude": 3.72,
                    },
                    "rules": [
                        {
                            "job_type_limitations": {
                                "Initial Appointment": 10,
                                "Wound Care": 5,
                            },
                            "max_drive_time": 10800,
                            "max_job_complexity": 0,
                            "max_service_time": 21600,
                            "max_work_time": 28800,
                            "min_drive_time": 3600,
                            "min_job_complexity": 0,
                            "min_service_time": 7200,
                            "min_work_time": 14400,
                            "period": {
                                "end": "2007-12-31T17:00:00",
                                "from": parse_datetime("2024-01-01T08:00:00Z"),
                                "to": parse_datetime("2024-01-07T17:00:00Z"),
                            },
                        }
                    ],
                    "start": {
                        "h3_index": 617700169958293500,
                        "latitude": 50.0987624,
                        "longitude": 4.93849204,
                    },
                    "tags": ["plumbing", "electrical"],
                }
            ],
            millis="millis",
            custom_distance_matrices={
                "matrix_service_url": "https://custom-matrix-service.com/api",
                "profile_matrices": {
                    "CAR": {
                        "6": "matrix-car-morning-123",
                        "9": "matrix-car-midday-456",
                        "16": "matrix-car-evening-789",
                    },
                    "TRUCK": {
                        "6": "matrix-truck-morning-abc",
                        "9": "matrix-truck-midday-def",
                    },
                },
            },
            hook="https://example.com",
            label="label",
            options={
                "clustering_threshold_meters": 10000,
                "enable_clustering": False,
                "euclidian": False,
                "explanation": {
                    "enabled": True,
                    "filter_hard_constraints": True,
                    "only_unassigned": True,
                },
                "fair_complexity_per_resource": True,
                "fair_complexity_per_trip": True,
                "fair_workload_per_resource": False,
                "fair_workload_per_trip": False,
                "job_proximity_distance_type": "HAVERSINE",
                "job_proximity_radius": 5000,
                "max_suggestions": 3,
                "minimize_resources": True,
                "only_feasible_suggestions": True,
                "partial_planning": True,
                "polylines": True,
                "routing_engine": "OSM",
                "snap_unit": 300,
                "traffic": 1.1,
                "workload_sensitivity": 0.1,
            },
            relations=[
                {
                    "jobs": ["Job-1", "Job-2"],
                    "time_interval": "FROM_ARRIVAL",
                    "type": "SEQUENCE",
                    "enforce_compatibility": True,
                    "hard_min_wait": True,
                    "max_time_interval": 3600,
                    "max_waiting_time": 1200,
                    "min_time_interval": 0,
                    "partial_planning": False,
                    "resource": "vehicle-1",
                    "tags": ["urgent"],
                    "weight": 1,
                }
            ],
            weights={
                "allowed_resources_weight": 500,
                "asap_weight": 5,
                "clustering_weight": 1,
                "drive_time_weight": 1,
                "job_proximity_weight": 1000,
                "minimize_resources_weight": 0,
                "planned_weight": 1000,
                "priority_weight": 100,
                "ranking_weight": 10,
                "travel_time_weight": 1,
                "urgency_weight": 50,
                "wait_time_weight": 1,
                "workload_spread_weight": 10,
            },
        )
        assert_matches_type(SolviceStatusJob, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_suggest(self, client: SolviceVrpSolver) -> None:
        response = client.vrp.with_raw_response.suggest(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        vrp = response.parse()
        assert_matches_type(SolviceStatusJob, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_suggest(self, client: SolviceVrpSolver) -> None:
        with client.vrp.with_streaming_response.suggest(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            vrp = response.parse()
            assert_matches_type(SolviceStatusJob, vrp, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_sync_evaluate(self, client: SolviceVrpSolver) -> None:
        vrp = client.vrp.sync_evaluate(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        )
        assert_matches_type(OnRouteResponse, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_sync_evaluate_with_all_params(self, client: SolviceVrpSolver) -> None:
        vrp = client.vrp.sync_evaluate(
            jobs=[
                {
                    "name": "Job-1",
                    "allowed_resources": ["string"],
                    "complexity": 1,
                    "disallowed_resources": ["vehicle-3", "vehicle-4"],
                    "duration": 600,
                    "duration_squash": 30,
                    "hard": True,
                    "hard_weight": 1,
                    "initial_arrival": "2023-01-13T09:00:00Z",
                    "initial_resource": "vehicle-1",
                    "job_types": ["Initial Appointment", "Wound Care"],
                    "load": [5, 10],
                    "location": {
                        "h3_index": 617700169958293500,
                        "latitude": 51.0543,
                        "longitude": 3.7174,
                    },
                    "padding": 300,
                    "planned_arrival": "2023-01-13T09:00:00Z",
                    "planned_date": "2023-01-13",
                    "planned_resource": "vehicle-1",
                    "priority": 100,
                    "proficiency": [
                        {
                            "resource": "senior-technician",
                            "duration_modifier": 0.8,
                        }
                    ],
                    "rankings": [
                        {
                            "name": "certified-technician",
                            "ranking": 5,
                        }
                    ],
                    "resumable": True,
                    "tags": [
                        {
                            "name": "plumbing",
                            "hard": False,
                            "weight": 300,
                        }
                    ],
                    "urgency": 80,
                    "windows": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T12:00:00Z",
                            "hard": True,
                            "weight": 1,
                        }
                    ],
                }
            ],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                            "breaks": [{"type": "WINDOWED"}],
                            "end": {
                                "h3_index": 617700169958293500,
                                "latitude": 51.0543,
                                "longitude": 3.7174,
                            },
                            "ignore_travel_time_from_last_job": False,
                            "ignore_travel_time_to_first_job": False,
                            "job_type_limitations": {
                                "Initial Appointment": 2,
                                "Wound Care": 1,
                            },
                            "overtime": {},
                            "overtime_end": "2023-01-13T19:00:00Z",
                            "start": {
                                "h3_index": 617700169958293500,
                                "latitude": 51.0543,
                                "longitude": 3.7174,
                            },
                            "tags": ["delivery", "installation"],
                        }
                    ],
                    "capacity": [500, 200],
                    "category": "CAR",
                    "compatible_resources": ["driver2", "driver3"],
                    "end": {
                        "h3_index": 617700169958293500,
                        "latitude": 50.0987624,
                        "longitude": 4.93849204,
                    },
                    "hourly_cost": 25,
                    "max_drive_distance": 0,
                    "max_drive_time": 0,
                    "max_drive_time_in_seconds": 28800,
                    "max_drive_time_job": 7200,
                    "region": {
                        "h3_index": 617700169958293500,
                        "latitude": 51.05,
                        "longitude": 3.72,
                    },
                    "rules": [
                        {
                            "job_type_limitations": {
                                "Initial Appointment": 10,
                                "Wound Care": 5,
                            },
                            "max_drive_time": 10800,
                            "max_job_complexity": 0,
                            "max_service_time": 21600,
                            "max_work_time": 28800,
                            "min_drive_time": 3600,
                            "min_job_complexity": 0,
                            "min_service_time": 7200,
                            "min_work_time": 14400,
                            "period": {
                                "end": "2007-12-31T17:00:00",
                                "from": parse_datetime("2024-01-01T08:00:00Z"),
                                "to": parse_datetime("2024-01-07T17:00:00Z"),
                            },
                        }
                    ],
                    "start": {
                        "h3_index": 617700169958293500,
                        "latitude": 50.0987624,
                        "longitude": 4.93849204,
                    },
                    "tags": ["plumbing", "electrical"],
                }
            ],
            custom_distance_matrices={
                "matrix_service_url": "https://custom-matrix-service.com/api",
                "profile_matrices": {
                    "CAR": {
                        "6": "matrix-car-morning-123",
                        "9": "matrix-car-midday-456",
                        "16": "matrix-car-evening-789",
                    },
                    "TRUCK": {
                        "6": "matrix-truck-morning-abc",
                        "9": "matrix-truck-midday-def",
                    },
                },
            },
            hook="https://example.com",
            label="label",
            options={
                "clustering_threshold_meters": 10000,
                "enable_clustering": False,
                "euclidian": False,
                "explanation": {
                    "enabled": True,
                    "filter_hard_constraints": True,
                    "only_unassigned": True,
                },
                "fair_complexity_per_resource": True,
                "fair_complexity_per_trip": True,
                "fair_workload_per_resource": False,
                "fair_workload_per_trip": False,
                "job_proximity_distance_type": "HAVERSINE",
                "job_proximity_radius": 5000,
                "max_suggestions": 3,
                "minimize_resources": True,
                "only_feasible_suggestions": True,
                "partial_planning": True,
                "polylines": True,
                "routing_engine": "OSM",
                "snap_unit": 300,
                "traffic": 1.1,
                "workload_sensitivity": 0.1,
            },
            relations=[
                {
                    "jobs": ["Job-1", "Job-2"],
                    "time_interval": "FROM_ARRIVAL",
                    "type": "SEQUENCE",
                    "enforce_compatibility": True,
                    "hard_min_wait": True,
                    "max_time_interval": 3600,
                    "max_waiting_time": 1200,
                    "min_time_interval": 0,
                    "partial_planning": False,
                    "resource": "vehicle-1",
                    "tags": ["urgent"],
                    "weight": 1,
                }
            ],
            weights={
                "allowed_resources_weight": 500,
                "asap_weight": 5,
                "clustering_weight": 1,
                "drive_time_weight": 1,
                "job_proximity_weight": 1000,
                "minimize_resources_weight": 0,
                "planned_weight": 1000,
                "priority_weight": 100,
                "ranking_weight": 10,
                "travel_time_weight": 1,
                "urgency_weight": 50,
                "wait_time_weight": 1,
                "workload_spread_weight": 10,
            },
        )
        assert_matches_type(OnRouteResponse, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_sync_evaluate(self, client: SolviceVrpSolver) -> None:
        response = client.vrp.with_raw_response.sync_evaluate(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        vrp = response.parse()
        assert_matches_type(OnRouteResponse, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_sync_evaluate(self, client: SolviceVrpSolver) -> None:
        with client.vrp.with_streaming_response.sync_evaluate(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            vrp = response.parse()
            assert_matches_type(OnRouteResponse, vrp, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_sync_solve(self, client: SolviceVrpSolver) -> None:
        vrp = client.vrp.sync_solve(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        )
        assert_matches_type(OnRouteResponse, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_sync_solve_with_all_params(self, client: SolviceVrpSolver) -> None:
        vrp = client.vrp.sync_solve(
            jobs=[
                {
                    "name": "Job-1",
                    "allowed_resources": ["string"],
                    "complexity": 1,
                    "disallowed_resources": ["vehicle-3", "vehicle-4"],
                    "duration": 600,
                    "duration_squash": 30,
                    "hard": True,
                    "hard_weight": 1,
                    "initial_arrival": "2023-01-13T09:00:00Z",
                    "initial_resource": "vehicle-1",
                    "job_types": ["Initial Appointment", "Wound Care"],
                    "load": [5, 10],
                    "location": {
                        "h3_index": 617700169958293500,
                        "latitude": 51.0543,
                        "longitude": 3.7174,
                    },
                    "padding": 300,
                    "planned_arrival": "2023-01-13T09:00:00Z",
                    "planned_date": "2023-01-13",
                    "planned_resource": "vehicle-1",
                    "priority": 100,
                    "proficiency": [
                        {
                            "resource": "senior-technician",
                            "duration_modifier": 0.8,
                        }
                    ],
                    "rankings": [
                        {
                            "name": "certified-technician",
                            "ranking": 5,
                        }
                    ],
                    "resumable": True,
                    "tags": [
                        {
                            "name": "plumbing",
                            "hard": False,
                            "weight": 300,
                        }
                    ],
                    "urgency": 80,
                    "windows": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T12:00:00Z",
                            "hard": True,
                            "weight": 1,
                        }
                    ],
                }
            ],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                            "breaks": [{"type": "WINDOWED"}],
                            "end": {
                                "h3_index": 617700169958293500,
                                "latitude": 51.0543,
                                "longitude": 3.7174,
                            },
                            "ignore_travel_time_from_last_job": False,
                            "ignore_travel_time_to_first_job": False,
                            "job_type_limitations": {
                                "Initial Appointment": 2,
                                "Wound Care": 1,
                            },
                            "overtime": {},
                            "overtime_end": "2023-01-13T19:00:00Z",
                            "start": {
                                "h3_index": 617700169958293500,
                                "latitude": 51.0543,
                                "longitude": 3.7174,
                            },
                            "tags": ["delivery", "installation"],
                        }
                    ],
                    "capacity": [500, 200],
                    "category": "CAR",
                    "compatible_resources": ["driver2", "driver3"],
                    "end": {
                        "h3_index": 617700169958293500,
                        "latitude": 50.0987624,
                        "longitude": 4.93849204,
                    },
                    "hourly_cost": 25,
                    "max_drive_distance": 0,
                    "max_drive_time": 0,
                    "max_drive_time_in_seconds": 28800,
                    "max_drive_time_job": 7200,
                    "region": {
                        "h3_index": 617700169958293500,
                        "latitude": 51.05,
                        "longitude": 3.72,
                    },
                    "rules": [
                        {
                            "job_type_limitations": {
                                "Initial Appointment": 10,
                                "Wound Care": 5,
                            },
                            "max_drive_time": 10800,
                            "max_job_complexity": 0,
                            "max_service_time": 21600,
                            "max_work_time": 28800,
                            "min_drive_time": 3600,
                            "min_job_complexity": 0,
                            "min_service_time": 7200,
                            "min_work_time": 14400,
                            "period": {
                                "end": "2007-12-31T17:00:00",
                                "from": parse_datetime("2024-01-01T08:00:00Z"),
                                "to": parse_datetime("2024-01-07T17:00:00Z"),
                            },
                        }
                    ],
                    "start": {
                        "h3_index": 617700169958293500,
                        "latitude": 50.0987624,
                        "longitude": 4.93849204,
                    },
                    "tags": ["plumbing", "electrical"],
                }
            ],
            millis="millis",
            custom_distance_matrices={
                "matrix_service_url": "https://custom-matrix-service.com/api",
                "profile_matrices": {
                    "CAR": {
                        "6": "matrix-car-morning-123",
                        "9": "matrix-car-midday-456",
                        "16": "matrix-car-evening-789",
                    },
                    "TRUCK": {
                        "6": "matrix-truck-morning-abc",
                        "9": "matrix-truck-midday-def",
                    },
                },
            },
            hook="https://example.com",
            label="label",
            options={
                "clustering_threshold_meters": 10000,
                "enable_clustering": False,
                "euclidian": False,
                "explanation": {
                    "enabled": True,
                    "filter_hard_constraints": True,
                    "only_unassigned": True,
                },
                "fair_complexity_per_resource": True,
                "fair_complexity_per_trip": True,
                "fair_workload_per_resource": False,
                "fair_workload_per_trip": False,
                "job_proximity_distance_type": "HAVERSINE",
                "job_proximity_radius": 5000,
                "max_suggestions": 3,
                "minimize_resources": True,
                "only_feasible_suggestions": True,
                "partial_planning": True,
                "polylines": True,
                "routing_engine": "OSM",
                "snap_unit": 300,
                "traffic": 1.1,
                "workload_sensitivity": 0.1,
            },
            relations=[
                {
                    "jobs": ["Job-1", "Job-2"],
                    "time_interval": "FROM_ARRIVAL",
                    "type": "SEQUENCE",
                    "enforce_compatibility": True,
                    "hard_min_wait": True,
                    "max_time_interval": 3600,
                    "max_waiting_time": 1200,
                    "min_time_interval": 0,
                    "partial_planning": False,
                    "resource": "vehicle-1",
                    "tags": ["urgent"],
                    "weight": 1,
                }
            ],
            weights={
                "allowed_resources_weight": 500,
                "asap_weight": 5,
                "clustering_weight": 1,
                "drive_time_weight": 1,
                "job_proximity_weight": 1000,
                "minimize_resources_weight": 0,
                "planned_weight": 1000,
                "priority_weight": 100,
                "ranking_weight": 10,
                "travel_time_weight": 1,
                "urgency_weight": 50,
                "wait_time_weight": 1,
                "workload_spread_weight": 10,
            },
        )
        assert_matches_type(OnRouteResponse, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_sync_solve(self, client: SolviceVrpSolver) -> None:
        response = client.vrp.with_raw_response.sync_solve(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        vrp = response.parse()
        assert_matches_type(OnRouteResponse, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_sync_solve(self, client: SolviceVrpSolver) -> None:
        with client.vrp.with_streaming_response.sync_solve(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            vrp = response.parse()
            assert_matches_type(OnRouteResponse, vrp, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_sync_suggest(self, client: SolviceVrpSolver) -> None:
        vrp = client.vrp.sync_suggest(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        )
        assert_matches_type(OnRouteResponse, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_sync_suggest_with_all_params(self, client: SolviceVrpSolver) -> None:
        vrp = client.vrp.sync_suggest(
            jobs=[
                {
                    "name": "Job-1",
                    "allowed_resources": ["string"],
                    "complexity": 1,
                    "disallowed_resources": ["vehicle-3", "vehicle-4"],
                    "duration": 600,
                    "duration_squash": 30,
                    "hard": True,
                    "hard_weight": 1,
                    "initial_arrival": "2023-01-13T09:00:00Z",
                    "initial_resource": "vehicle-1",
                    "job_types": ["Initial Appointment", "Wound Care"],
                    "load": [5, 10],
                    "location": {
                        "h3_index": 617700169958293500,
                        "latitude": 51.0543,
                        "longitude": 3.7174,
                    },
                    "padding": 300,
                    "planned_arrival": "2023-01-13T09:00:00Z",
                    "planned_date": "2023-01-13",
                    "planned_resource": "vehicle-1",
                    "priority": 100,
                    "proficiency": [
                        {
                            "resource": "senior-technician",
                            "duration_modifier": 0.8,
                        }
                    ],
                    "rankings": [
                        {
                            "name": "certified-technician",
                            "ranking": 5,
                        }
                    ],
                    "resumable": True,
                    "tags": [
                        {
                            "name": "plumbing",
                            "hard": False,
                            "weight": 300,
                        }
                    ],
                    "urgency": 80,
                    "windows": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T12:00:00Z",
                            "hard": True,
                            "weight": 1,
                        }
                    ],
                }
            ],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                            "breaks": [{"type": "WINDOWED"}],
                            "end": {
                                "h3_index": 617700169958293500,
                                "latitude": 51.0543,
                                "longitude": 3.7174,
                            },
                            "ignore_travel_time_from_last_job": False,
                            "ignore_travel_time_to_first_job": False,
                            "job_type_limitations": {
                                "Initial Appointment": 2,
                                "Wound Care": 1,
                            },
                            "overtime": {},
                            "overtime_end": "2023-01-13T19:00:00Z",
                            "start": {
                                "h3_index": 617700169958293500,
                                "latitude": 51.0543,
                                "longitude": 3.7174,
                            },
                            "tags": ["delivery", "installation"],
                        }
                    ],
                    "capacity": [500, 200],
                    "category": "CAR",
                    "compatible_resources": ["driver2", "driver3"],
                    "end": {
                        "h3_index": 617700169958293500,
                        "latitude": 50.0987624,
                        "longitude": 4.93849204,
                    },
                    "hourly_cost": 25,
                    "max_drive_distance": 0,
                    "max_drive_time": 0,
                    "max_drive_time_in_seconds": 28800,
                    "max_drive_time_job": 7200,
                    "region": {
                        "h3_index": 617700169958293500,
                        "latitude": 51.05,
                        "longitude": 3.72,
                    },
                    "rules": [
                        {
                            "job_type_limitations": {
                                "Initial Appointment": 10,
                                "Wound Care": 5,
                            },
                            "max_drive_time": 10800,
                            "max_job_complexity": 0,
                            "max_service_time": 21600,
                            "max_work_time": 28800,
                            "min_drive_time": 3600,
                            "min_job_complexity": 0,
                            "min_service_time": 7200,
                            "min_work_time": 14400,
                            "period": {
                                "end": "2007-12-31T17:00:00",
                                "from": parse_datetime("2024-01-01T08:00:00Z"),
                                "to": parse_datetime("2024-01-07T17:00:00Z"),
                            },
                        }
                    ],
                    "start": {
                        "h3_index": 617700169958293500,
                        "latitude": 50.0987624,
                        "longitude": 4.93849204,
                    },
                    "tags": ["plumbing", "electrical"],
                }
            ],
            millis="millis",
            custom_distance_matrices={
                "matrix_service_url": "https://custom-matrix-service.com/api",
                "profile_matrices": {
                    "CAR": {
                        "6": "matrix-car-morning-123",
                        "9": "matrix-car-midday-456",
                        "16": "matrix-car-evening-789",
                    },
                    "TRUCK": {
                        "6": "matrix-truck-morning-abc",
                        "9": "matrix-truck-midday-def",
                    },
                },
            },
            hook="https://example.com",
            label="label",
            options={
                "clustering_threshold_meters": 10000,
                "enable_clustering": False,
                "euclidian": False,
                "explanation": {
                    "enabled": True,
                    "filter_hard_constraints": True,
                    "only_unassigned": True,
                },
                "fair_complexity_per_resource": True,
                "fair_complexity_per_trip": True,
                "fair_workload_per_resource": False,
                "fair_workload_per_trip": False,
                "job_proximity_distance_type": "HAVERSINE",
                "job_proximity_radius": 5000,
                "max_suggestions": 3,
                "minimize_resources": True,
                "only_feasible_suggestions": True,
                "partial_planning": True,
                "polylines": True,
                "routing_engine": "OSM",
                "snap_unit": 300,
                "traffic": 1.1,
                "workload_sensitivity": 0.1,
            },
            relations=[
                {
                    "jobs": ["Job-1", "Job-2"],
                    "time_interval": "FROM_ARRIVAL",
                    "type": "SEQUENCE",
                    "enforce_compatibility": True,
                    "hard_min_wait": True,
                    "max_time_interval": 3600,
                    "max_waiting_time": 1200,
                    "min_time_interval": 0,
                    "partial_planning": False,
                    "resource": "vehicle-1",
                    "tags": ["urgent"],
                    "weight": 1,
                }
            ],
            weights={
                "allowed_resources_weight": 500,
                "asap_weight": 5,
                "clustering_weight": 1,
                "drive_time_weight": 1,
                "job_proximity_weight": 1000,
                "minimize_resources_weight": 0,
                "planned_weight": 1000,
                "priority_weight": 100,
                "ranking_weight": 10,
                "travel_time_weight": 1,
                "urgency_weight": 50,
                "wait_time_weight": 1,
                "workload_spread_weight": 10,
            },
        )
        assert_matches_type(OnRouteResponse, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_sync_suggest(self, client: SolviceVrpSolver) -> None:
        response = client.vrp.with_raw_response.sync_suggest(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        vrp = response.parse()
        assert_matches_type(OnRouteResponse, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_sync_suggest(self, client: SolviceVrpSolver) -> None:
        with client.vrp.with_streaming_response.sync_suggest(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            vrp = response.parse()
            assert_matches_type(OnRouteResponse, vrp, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncVrp:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_demo(self, async_client: AsyncSolviceVrpSolver) -> None:
        vrp = await async_client.vrp.demo()
        assert_matches_type(Request, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_demo_with_all_params(self, async_client: AsyncSolviceVrpSolver) -> None:
        vrp = await async_client.vrp.demo(
            geolocation="geolocation",
            jobs=0,
            radius=0,
        )
        assert_matches_type(Request, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_demo(self, async_client: AsyncSolviceVrpSolver) -> None:
        response = await async_client.vrp.with_raw_response.demo()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        vrp = await response.parse()
        assert_matches_type(Request, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_demo(self, async_client: AsyncSolviceVrpSolver) -> None:
        async with async_client.vrp.with_streaming_response.demo() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            vrp = await response.parse()
            assert_matches_type(Request, vrp, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_evaluate(self, async_client: AsyncSolviceVrpSolver) -> None:
        vrp = await async_client.vrp.evaluate(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        )
        assert_matches_type(SolviceStatusJob, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_evaluate_with_all_params(self, async_client: AsyncSolviceVrpSolver) -> None:
        vrp = await async_client.vrp.evaluate(
            jobs=[
                {
                    "name": "Job-1",
                    "allowed_resources": ["string"],
                    "complexity": 1,
                    "disallowed_resources": ["vehicle-3", "vehicle-4"],
                    "duration": 600,
                    "duration_squash": 30,
                    "hard": True,
                    "hard_weight": 1,
                    "initial_arrival": "2023-01-13T09:00:00Z",
                    "initial_resource": "vehicle-1",
                    "job_types": ["Initial Appointment", "Wound Care"],
                    "load": [5, 10],
                    "location": {
                        "h3_index": 617700169958293500,
                        "latitude": 51.0543,
                        "longitude": 3.7174,
                    },
                    "padding": 300,
                    "planned_arrival": "2023-01-13T09:00:00Z",
                    "planned_date": "2023-01-13",
                    "planned_resource": "vehicle-1",
                    "priority": 100,
                    "proficiency": [
                        {
                            "resource": "senior-technician",
                            "duration_modifier": 0.8,
                        }
                    ],
                    "rankings": [
                        {
                            "name": "certified-technician",
                            "ranking": 5,
                        }
                    ],
                    "resumable": True,
                    "tags": [
                        {
                            "name": "plumbing",
                            "hard": False,
                            "weight": 300,
                        }
                    ],
                    "urgency": 80,
                    "windows": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T12:00:00Z",
                            "hard": True,
                            "weight": 1,
                        }
                    ],
                }
            ],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                            "breaks": [{"type": "WINDOWED"}],
                            "end": {
                                "h3_index": 617700169958293500,
                                "latitude": 51.0543,
                                "longitude": 3.7174,
                            },
                            "ignore_travel_time_from_last_job": False,
                            "ignore_travel_time_to_first_job": False,
                            "job_type_limitations": {
                                "Initial Appointment": 2,
                                "Wound Care": 1,
                            },
                            "overtime": {},
                            "overtime_end": "2023-01-13T19:00:00Z",
                            "start": {
                                "h3_index": 617700169958293500,
                                "latitude": 51.0543,
                                "longitude": 3.7174,
                            },
                            "tags": ["delivery", "installation"],
                        }
                    ],
                    "capacity": [500, 200],
                    "category": "CAR",
                    "compatible_resources": ["driver2", "driver3"],
                    "end": {
                        "h3_index": 617700169958293500,
                        "latitude": 50.0987624,
                        "longitude": 4.93849204,
                    },
                    "hourly_cost": 25,
                    "max_drive_distance": 0,
                    "max_drive_time": 0,
                    "max_drive_time_in_seconds": 28800,
                    "max_drive_time_job": 7200,
                    "region": {
                        "h3_index": 617700169958293500,
                        "latitude": 51.05,
                        "longitude": 3.72,
                    },
                    "rules": [
                        {
                            "job_type_limitations": {
                                "Initial Appointment": 10,
                                "Wound Care": 5,
                            },
                            "max_drive_time": 10800,
                            "max_job_complexity": 0,
                            "max_service_time": 21600,
                            "max_work_time": 28800,
                            "min_drive_time": 3600,
                            "min_job_complexity": 0,
                            "min_service_time": 7200,
                            "min_work_time": 14400,
                            "period": {
                                "end": "2007-12-31T17:00:00",
                                "from": parse_datetime("2024-01-01T08:00:00Z"),
                                "to": parse_datetime("2024-01-07T17:00:00Z"),
                            },
                        }
                    ],
                    "start": {
                        "h3_index": 617700169958293500,
                        "latitude": 50.0987624,
                        "longitude": 4.93849204,
                    },
                    "tags": ["plumbing", "electrical"],
                }
            ],
            custom_distance_matrices={
                "matrix_service_url": "https://custom-matrix-service.com/api",
                "profile_matrices": {
                    "CAR": {
                        "6": "matrix-car-morning-123",
                        "9": "matrix-car-midday-456",
                        "16": "matrix-car-evening-789",
                    },
                    "TRUCK": {
                        "6": "matrix-truck-morning-abc",
                        "9": "matrix-truck-midday-def",
                    },
                },
            },
            hook="https://example.com",
            label="label",
            options={
                "clustering_threshold_meters": 10000,
                "enable_clustering": False,
                "euclidian": False,
                "explanation": {
                    "enabled": True,
                    "filter_hard_constraints": True,
                    "only_unassigned": True,
                },
                "fair_complexity_per_resource": True,
                "fair_complexity_per_trip": True,
                "fair_workload_per_resource": False,
                "fair_workload_per_trip": False,
                "job_proximity_distance_type": "HAVERSINE",
                "job_proximity_radius": 5000,
                "max_suggestions": 3,
                "minimize_resources": True,
                "only_feasible_suggestions": True,
                "partial_planning": True,
                "polylines": True,
                "routing_engine": "OSM",
                "snap_unit": 300,
                "traffic": 1.1,
                "workload_sensitivity": 0.1,
            },
            relations=[
                {
                    "jobs": ["Job-1", "Job-2"],
                    "time_interval": "FROM_ARRIVAL",
                    "type": "SEQUENCE",
                    "enforce_compatibility": True,
                    "hard_min_wait": True,
                    "max_time_interval": 3600,
                    "max_waiting_time": 1200,
                    "min_time_interval": 0,
                    "partial_planning": False,
                    "resource": "vehicle-1",
                    "tags": ["urgent"],
                    "weight": 1,
                }
            ],
            weights={
                "allowed_resources_weight": 500,
                "asap_weight": 5,
                "clustering_weight": 1,
                "drive_time_weight": 1,
                "job_proximity_weight": 1000,
                "minimize_resources_weight": 0,
                "planned_weight": 1000,
                "priority_weight": 100,
                "ranking_weight": 10,
                "travel_time_weight": 1,
                "urgency_weight": 50,
                "wait_time_weight": 1,
                "workload_spread_weight": 10,
            },
        )
        assert_matches_type(SolviceStatusJob, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_evaluate(self, async_client: AsyncSolviceVrpSolver) -> None:
        response = await async_client.vrp.with_raw_response.evaluate(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        vrp = await response.parse()
        assert_matches_type(SolviceStatusJob, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_evaluate(self, async_client: AsyncSolviceVrpSolver) -> None:
        async with async_client.vrp.with_streaming_response.evaluate(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            vrp = await response.parse()
            assert_matches_type(SolviceStatusJob, vrp, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_solve(self, async_client: AsyncSolviceVrpSolver) -> None:
        vrp = await async_client.vrp.solve(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        )
        assert_matches_type(SolviceStatusJob, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_solve_with_all_params(self, async_client: AsyncSolviceVrpSolver) -> None:
        vrp = await async_client.vrp.solve(
            jobs=[
                {
                    "name": "Job-1",
                    "allowed_resources": ["string"],
                    "complexity": 1,
                    "disallowed_resources": ["vehicle-3", "vehicle-4"],
                    "duration": 600,
                    "duration_squash": 30,
                    "hard": True,
                    "hard_weight": 1,
                    "initial_arrival": "2023-01-13T09:00:00Z",
                    "initial_resource": "vehicle-1",
                    "job_types": ["Initial Appointment", "Wound Care"],
                    "load": [5, 10],
                    "location": {
                        "h3_index": 617700169958293500,
                        "latitude": 51.0543,
                        "longitude": 3.7174,
                    },
                    "padding": 300,
                    "planned_arrival": "2023-01-13T09:00:00Z",
                    "planned_date": "2023-01-13",
                    "planned_resource": "vehicle-1",
                    "priority": 100,
                    "proficiency": [
                        {
                            "resource": "senior-technician",
                            "duration_modifier": 0.8,
                        }
                    ],
                    "rankings": [
                        {
                            "name": "certified-technician",
                            "ranking": 5,
                        }
                    ],
                    "resumable": True,
                    "tags": [
                        {
                            "name": "plumbing",
                            "hard": False,
                            "weight": 300,
                        }
                    ],
                    "urgency": 80,
                    "windows": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T12:00:00Z",
                            "hard": True,
                            "weight": 1,
                        }
                    ],
                }
            ],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                            "breaks": [{"type": "WINDOWED"}],
                            "end": {
                                "h3_index": 617700169958293500,
                                "latitude": 51.0543,
                                "longitude": 3.7174,
                            },
                            "ignore_travel_time_from_last_job": False,
                            "ignore_travel_time_to_first_job": False,
                            "job_type_limitations": {
                                "Initial Appointment": 2,
                                "Wound Care": 1,
                            },
                            "overtime": {},
                            "overtime_end": "2023-01-13T19:00:00Z",
                            "start": {
                                "h3_index": 617700169958293500,
                                "latitude": 51.0543,
                                "longitude": 3.7174,
                            },
                            "tags": ["delivery", "installation"],
                        }
                    ],
                    "capacity": [500, 200],
                    "category": "CAR",
                    "compatible_resources": ["driver2", "driver3"],
                    "end": {
                        "h3_index": 617700169958293500,
                        "latitude": 50.0987624,
                        "longitude": 4.93849204,
                    },
                    "hourly_cost": 25,
                    "max_drive_distance": 0,
                    "max_drive_time": 0,
                    "max_drive_time_in_seconds": 28800,
                    "max_drive_time_job": 7200,
                    "region": {
                        "h3_index": 617700169958293500,
                        "latitude": 51.05,
                        "longitude": 3.72,
                    },
                    "rules": [
                        {
                            "job_type_limitations": {
                                "Initial Appointment": 10,
                                "Wound Care": 5,
                            },
                            "max_drive_time": 10800,
                            "max_job_complexity": 0,
                            "max_service_time": 21600,
                            "max_work_time": 28800,
                            "min_drive_time": 3600,
                            "min_job_complexity": 0,
                            "min_service_time": 7200,
                            "min_work_time": 14400,
                            "period": {
                                "end": "2007-12-31T17:00:00",
                                "from": parse_datetime("2024-01-01T08:00:00Z"),
                                "to": parse_datetime("2024-01-07T17:00:00Z"),
                            },
                        }
                    ],
                    "start": {
                        "h3_index": 617700169958293500,
                        "latitude": 50.0987624,
                        "longitude": 4.93849204,
                    },
                    "tags": ["plumbing", "electrical"],
                }
            ],
            millis="millis",
            custom_distance_matrices={
                "matrix_service_url": "https://custom-matrix-service.com/api",
                "profile_matrices": {
                    "CAR": {
                        "6": "matrix-car-morning-123",
                        "9": "matrix-car-midday-456",
                        "16": "matrix-car-evening-789",
                    },
                    "TRUCK": {
                        "6": "matrix-truck-morning-abc",
                        "9": "matrix-truck-midday-def",
                    },
                },
            },
            hook="https://example.com",
            label="label",
            options={
                "clustering_threshold_meters": 10000,
                "enable_clustering": False,
                "euclidian": False,
                "explanation": {
                    "enabled": True,
                    "filter_hard_constraints": True,
                    "only_unassigned": True,
                },
                "fair_complexity_per_resource": True,
                "fair_complexity_per_trip": True,
                "fair_workload_per_resource": False,
                "fair_workload_per_trip": False,
                "job_proximity_distance_type": "HAVERSINE",
                "job_proximity_radius": 5000,
                "max_suggestions": 3,
                "minimize_resources": True,
                "only_feasible_suggestions": True,
                "partial_planning": True,
                "polylines": True,
                "routing_engine": "OSM",
                "snap_unit": 300,
                "traffic": 1.1,
                "workload_sensitivity": 0.1,
            },
            relations=[
                {
                    "jobs": ["Job-1", "Job-2"],
                    "time_interval": "FROM_ARRIVAL",
                    "type": "SEQUENCE",
                    "enforce_compatibility": True,
                    "hard_min_wait": True,
                    "max_time_interval": 3600,
                    "max_waiting_time": 1200,
                    "min_time_interval": 0,
                    "partial_planning": False,
                    "resource": "vehicle-1",
                    "tags": ["urgent"],
                    "weight": 1,
                }
            ],
            weights={
                "allowed_resources_weight": 500,
                "asap_weight": 5,
                "clustering_weight": 1,
                "drive_time_weight": 1,
                "job_proximity_weight": 1000,
                "minimize_resources_weight": 0,
                "planned_weight": 1000,
                "priority_weight": 100,
                "ranking_weight": 10,
                "travel_time_weight": 1,
                "urgency_weight": 50,
                "wait_time_weight": 1,
                "workload_spread_weight": 10,
            },
            instance="instance",
        )
        assert_matches_type(SolviceStatusJob, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_solve(self, async_client: AsyncSolviceVrpSolver) -> None:
        response = await async_client.vrp.with_raw_response.solve(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        vrp = await response.parse()
        assert_matches_type(SolviceStatusJob, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_solve(self, async_client: AsyncSolviceVrpSolver) -> None:
        async with async_client.vrp.with_streaming_response.solve(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            vrp = await response.parse()
            assert_matches_type(SolviceStatusJob, vrp, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_suggest(self, async_client: AsyncSolviceVrpSolver) -> None:
        vrp = await async_client.vrp.suggest(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        )
        assert_matches_type(SolviceStatusJob, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_suggest_with_all_params(self, async_client: AsyncSolviceVrpSolver) -> None:
        vrp = await async_client.vrp.suggest(
            jobs=[
                {
                    "name": "Job-1",
                    "allowed_resources": ["string"],
                    "complexity": 1,
                    "disallowed_resources": ["vehicle-3", "vehicle-4"],
                    "duration": 600,
                    "duration_squash": 30,
                    "hard": True,
                    "hard_weight": 1,
                    "initial_arrival": "2023-01-13T09:00:00Z",
                    "initial_resource": "vehicle-1",
                    "job_types": ["Initial Appointment", "Wound Care"],
                    "load": [5, 10],
                    "location": {
                        "h3_index": 617700169958293500,
                        "latitude": 51.0543,
                        "longitude": 3.7174,
                    },
                    "padding": 300,
                    "planned_arrival": "2023-01-13T09:00:00Z",
                    "planned_date": "2023-01-13",
                    "planned_resource": "vehicle-1",
                    "priority": 100,
                    "proficiency": [
                        {
                            "resource": "senior-technician",
                            "duration_modifier": 0.8,
                        }
                    ],
                    "rankings": [
                        {
                            "name": "certified-technician",
                            "ranking": 5,
                        }
                    ],
                    "resumable": True,
                    "tags": [
                        {
                            "name": "plumbing",
                            "hard": False,
                            "weight": 300,
                        }
                    ],
                    "urgency": 80,
                    "windows": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T12:00:00Z",
                            "hard": True,
                            "weight": 1,
                        }
                    ],
                }
            ],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                            "breaks": [{"type": "WINDOWED"}],
                            "end": {
                                "h3_index": 617700169958293500,
                                "latitude": 51.0543,
                                "longitude": 3.7174,
                            },
                            "ignore_travel_time_from_last_job": False,
                            "ignore_travel_time_to_first_job": False,
                            "job_type_limitations": {
                                "Initial Appointment": 2,
                                "Wound Care": 1,
                            },
                            "overtime": {},
                            "overtime_end": "2023-01-13T19:00:00Z",
                            "start": {
                                "h3_index": 617700169958293500,
                                "latitude": 51.0543,
                                "longitude": 3.7174,
                            },
                            "tags": ["delivery", "installation"],
                        }
                    ],
                    "capacity": [500, 200],
                    "category": "CAR",
                    "compatible_resources": ["driver2", "driver3"],
                    "end": {
                        "h3_index": 617700169958293500,
                        "latitude": 50.0987624,
                        "longitude": 4.93849204,
                    },
                    "hourly_cost": 25,
                    "max_drive_distance": 0,
                    "max_drive_time": 0,
                    "max_drive_time_in_seconds": 28800,
                    "max_drive_time_job": 7200,
                    "region": {
                        "h3_index": 617700169958293500,
                        "latitude": 51.05,
                        "longitude": 3.72,
                    },
                    "rules": [
                        {
                            "job_type_limitations": {
                                "Initial Appointment": 10,
                                "Wound Care": 5,
                            },
                            "max_drive_time": 10800,
                            "max_job_complexity": 0,
                            "max_service_time": 21600,
                            "max_work_time": 28800,
                            "min_drive_time": 3600,
                            "min_job_complexity": 0,
                            "min_service_time": 7200,
                            "min_work_time": 14400,
                            "period": {
                                "end": "2007-12-31T17:00:00",
                                "from": parse_datetime("2024-01-01T08:00:00Z"),
                                "to": parse_datetime("2024-01-07T17:00:00Z"),
                            },
                        }
                    ],
                    "start": {
                        "h3_index": 617700169958293500,
                        "latitude": 50.0987624,
                        "longitude": 4.93849204,
                    },
                    "tags": ["plumbing", "electrical"],
                }
            ],
            millis="millis",
            custom_distance_matrices={
                "matrix_service_url": "https://custom-matrix-service.com/api",
                "profile_matrices": {
                    "CAR": {
                        "6": "matrix-car-morning-123",
                        "9": "matrix-car-midday-456",
                        "16": "matrix-car-evening-789",
                    },
                    "TRUCK": {
                        "6": "matrix-truck-morning-abc",
                        "9": "matrix-truck-midday-def",
                    },
                },
            },
            hook="https://example.com",
            label="label",
            options={
                "clustering_threshold_meters": 10000,
                "enable_clustering": False,
                "euclidian": False,
                "explanation": {
                    "enabled": True,
                    "filter_hard_constraints": True,
                    "only_unassigned": True,
                },
                "fair_complexity_per_resource": True,
                "fair_complexity_per_trip": True,
                "fair_workload_per_resource": False,
                "fair_workload_per_trip": False,
                "job_proximity_distance_type": "HAVERSINE",
                "job_proximity_radius": 5000,
                "max_suggestions": 3,
                "minimize_resources": True,
                "only_feasible_suggestions": True,
                "partial_planning": True,
                "polylines": True,
                "routing_engine": "OSM",
                "snap_unit": 300,
                "traffic": 1.1,
                "workload_sensitivity": 0.1,
            },
            relations=[
                {
                    "jobs": ["Job-1", "Job-2"],
                    "time_interval": "FROM_ARRIVAL",
                    "type": "SEQUENCE",
                    "enforce_compatibility": True,
                    "hard_min_wait": True,
                    "max_time_interval": 3600,
                    "max_waiting_time": 1200,
                    "min_time_interval": 0,
                    "partial_planning": False,
                    "resource": "vehicle-1",
                    "tags": ["urgent"],
                    "weight": 1,
                }
            ],
            weights={
                "allowed_resources_weight": 500,
                "asap_weight": 5,
                "clustering_weight": 1,
                "drive_time_weight": 1,
                "job_proximity_weight": 1000,
                "minimize_resources_weight": 0,
                "planned_weight": 1000,
                "priority_weight": 100,
                "ranking_weight": 10,
                "travel_time_weight": 1,
                "urgency_weight": 50,
                "wait_time_weight": 1,
                "workload_spread_weight": 10,
            },
        )
        assert_matches_type(SolviceStatusJob, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_suggest(self, async_client: AsyncSolviceVrpSolver) -> None:
        response = await async_client.vrp.with_raw_response.suggest(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        vrp = await response.parse()
        assert_matches_type(SolviceStatusJob, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_suggest(self, async_client: AsyncSolviceVrpSolver) -> None:
        async with async_client.vrp.with_streaming_response.suggest(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            vrp = await response.parse()
            assert_matches_type(SolviceStatusJob, vrp, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_sync_evaluate(self, async_client: AsyncSolviceVrpSolver) -> None:
        vrp = await async_client.vrp.sync_evaluate(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        )
        assert_matches_type(OnRouteResponse, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_sync_evaluate_with_all_params(self, async_client: AsyncSolviceVrpSolver) -> None:
        vrp = await async_client.vrp.sync_evaluate(
            jobs=[
                {
                    "name": "Job-1",
                    "allowed_resources": ["string"],
                    "complexity": 1,
                    "disallowed_resources": ["vehicle-3", "vehicle-4"],
                    "duration": 600,
                    "duration_squash": 30,
                    "hard": True,
                    "hard_weight": 1,
                    "initial_arrival": "2023-01-13T09:00:00Z",
                    "initial_resource": "vehicle-1",
                    "job_types": ["Initial Appointment", "Wound Care"],
                    "load": [5, 10],
                    "location": {
                        "h3_index": 617700169958293500,
                        "latitude": 51.0543,
                        "longitude": 3.7174,
                    },
                    "padding": 300,
                    "planned_arrival": "2023-01-13T09:00:00Z",
                    "planned_date": "2023-01-13",
                    "planned_resource": "vehicle-1",
                    "priority": 100,
                    "proficiency": [
                        {
                            "resource": "senior-technician",
                            "duration_modifier": 0.8,
                        }
                    ],
                    "rankings": [
                        {
                            "name": "certified-technician",
                            "ranking": 5,
                        }
                    ],
                    "resumable": True,
                    "tags": [
                        {
                            "name": "plumbing",
                            "hard": False,
                            "weight": 300,
                        }
                    ],
                    "urgency": 80,
                    "windows": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T12:00:00Z",
                            "hard": True,
                            "weight": 1,
                        }
                    ],
                }
            ],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                            "breaks": [{"type": "WINDOWED"}],
                            "end": {
                                "h3_index": 617700169958293500,
                                "latitude": 51.0543,
                                "longitude": 3.7174,
                            },
                            "ignore_travel_time_from_last_job": False,
                            "ignore_travel_time_to_first_job": False,
                            "job_type_limitations": {
                                "Initial Appointment": 2,
                                "Wound Care": 1,
                            },
                            "overtime": {},
                            "overtime_end": "2023-01-13T19:00:00Z",
                            "start": {
                                "h3_index": 617700169958293500,
                                "latitude": 51.0543,
                                "longitude": 3.7174,
                            },
                            "tags": ["delivery", "installation"],
                        }
                    ],
                    "capacity": [500, 200],
                    "category": "CAR",
                    "compatible_resources": ["driver2", "driver3"],
                    "end": {
                        "h3_index": 617700169958293500,
                        "latitude": 50.0987624,
                        "longitude": 4.93849204,
                    },
                    "hourly_cost": 25,
                    "max_drive_distance": 0,
                    "max_drive_time": 0,
                    "max_drive_time_in_seconds": 28800,
                    "max_drive_time_job": 7200,
                    "region": {
                        "h3_index": 617700169958293500,
                        "latitude": 51.05,
                        "longitude": 3.72,
                    },
                    "rules": [
                        {
                            "job_type_limitations": {
                                "Initial Appointment": 10,
                                "Wound Care": 5,
                            },
                            "max_drive_time": 10800,
                            "max_job_complexity": 0,
                            "max_service_time": 21600,
                            "max_work_time": 28800,
                            "min_drive_time": 3600,
                            "min_job_complexity": 0,
                            "min_service_time": 7200,
                            "min_work_time": 14400,
                            "period": {
                                "end": "2007-12-31T17:00:00",
                                "from": parse_datetime("2024-01-01T08:00:00Z"),
                                "to": parse_datetime("2024-01-07T17:00:00Z"),
                            },
                        }
                    ],
                    "start": {
                        "h3_index": 617700169958293500,
                        "latitude": 50.0987624,
                        "longitude": 4.93849204,
                    },
                    "tags": ["plumbing", "electrical"],
                }
            ],
            custom_distance_matrices={
                "matrix_service_url": "https://custom-matrix-service.com/api",
                "profile_matrices": {
                    "CAR": {
                        "6": "matrix-car-morning-123",
                        "9": "matrix-car-midday-456",
                        "16": "matrix-car-evening-789",
                    },
                    "TRUCK": {
                        "6": "matrix-truck-morning-abc",
                        "9": "matrix-truck-midday-def",
                    },
                },
            },
            hook="https://example.com",
            label="label",
            options={
                "clustering_threshold_meters": 10000,
                "enable_clustering": False,
                "euclidian": False,
                "explanation": {
                    "enabled": True,
                    "filter_hard_constraints": True,
                    "only_unassigned": True,
                },
                "fair_complexity_per_resource": True,
                "fair_complexity_per_trip": True,
                "fair_workload_per_resource": False,
                "fair_workload_per_trip": False,
                "job_proximity_distance_type": "HAVERSINE",
                "job_proximity_radius": 5000,
                "max_suggestions": 3,
                "minimize_resources": True,
                "only_feasible_suggestions": True,
                "partial_planning": True,
                "polylines": True,
                "routing_engine": "OSM",
                "snap_unit": 300,
                "traffic": 1.1,
                "workload_sensitivity": 0.1,
            },
            relations=[
                {
                    "jobs": ["Job-1", "Job-2"],
                    "time_interval": "FROM_ARRIVAL",
                    "type": "SEQUENCE",
                    "enforce_compatibility": True,
                    "hard_min_wait": True,
                    "max_time_interval": 3600,
                    "max_waiting_time": 1200,
                    "min_time_interval": 0,
                    "partial_planning": False,
                    "resource": "vehicle-1",
                    "tags": ["urgent"],
                    "weight": 1,
                }
            ],
            weights={
                "allowed_resources_weight": 500,
                "asap_weight": 5,
                "clustering_weight": 1,
                "drive_time_weight": 1,
                "job_proximity_weight": 1000,
                "minimize_resources_weight": 0,
                "planned_weight": 1000,
                "priority_weight": 100,
                "ranking_weight": 10,
                "travel_time_weight": 1,
                "urgency_weight": 50,
                "wait_time_weight": 1,
                "workload_spread_weight": 10,
            },
        )
        assert_matches_type(OnRouteResponse, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_sync_evaluate(self, async_client: AsyncSolviceVrpSolver) -> None:
        response = await async_client.vrp.with_raw_response.sync_evaluate(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        vrp = await response.parse()
        assert_matches_type(OnRouteResponse, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_sync_evaluate(self, async_client: AsyncSolviceVrpSolver) -> None:
        async with async_client.vrp.with_streaming_response.sync_evaluate(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            vrp = await response.parse()
            assert_matches_type(OnRouteResponse, vrp, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_sync_solve(self, async_client: AsyncSolviceVrpSolver) -> None:
        vrp = await async_client.vrp.sync_solve(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        )
        assert_matches_type(OnRouteResponse, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_sync_solve_with_all_params(self, async_client: AsyncSolviceVrpSolver) -> None:
        vrp = await async_client.vrp.sync_solve(
            jobs=[
                {
                    "name": "Job-1",
                    "allowed_resources": ["string"],
                    "complexity": 1,
                    "disallowed_resources": ["vehicle-3", "vehicle-4"],
                    "duration": 600,
                    "duration_squash": 30,
                    "hard": True,
                    "hard_weight": 1,
                    "initial_arrival": "2023-01-13T09:00:00Z",
                    "initial_resource": "vehicle-1",
                    "job_types": ["Initial Appointment", "Wound Care"],
                    "load": [5, 10],
                    "location": {
                        "h3_index": 617700169958293500,
                        "latitude": 51.0543,
                        "longitude": 3.7174,
                    },
                    "padding": 300,
                    "planned_arrival": "2023-01-13T09:00:00Z",
                    "planned_date": "2023-01-13",
                    "planned_resource": "vehicle-1",
                    "priority": 100,
                    "proficiency": [
                        {
                            "resource": "senior-technician",
                            "duration_modifier": 0.8,
                        }
                    ],
                    "rankings": [
                        {
                            "name": "certified-technician",
                            "ranking": 5,
                        }
                    ],
                    "resumable": True,
                    "tags": [
                        {
                            "name": "plumbing",
                            "hard": False,
                            "weight": 300,
                        }
                    ],
                    "urgency": 80,
                    "windows": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T12:00:00Z",
                            "hard": True,
                            "weight": 1,
                        }
                    ],
                }
            ],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                            "breaks": [{"type": "WINDOWED"}],
                            "end": {
                                "h3_index": 617700169958293500,
                                "latitude": 51.0543,
                                "longitude": 3.7174,
                            },
                            "ignore_travel_time_from_last_job": False,
                            "ignore_travel_time_to_first_job": False,
                            "job_type_limitations": {
                                "Initial Appointment": 2,
                                "Wound Care": 1,
                            },
                            "overtime": {},
                            "overtime_end": "2023-01-13T19:00:00Z",
                            "start": {
                                "h3_index": 617700169958293500,
                                "latitude": 51.0543,
                                "longitude": 3.7174,
                            },
                            "tags": ["delivery", "installation"],
                        }
                    ],
                    "capacity": [500, 200],
                    "category": "CAR",
                    "compatible_resources": ["driver2", "driver3"],
                    "end": {
                        "h3_index": 617700169958293500,
                        "latitude": 50.0987624,
                        "longitude": 4.93849204,
                    },
                    "hourly_cost": 25,
                    "max_drive_distance": 0,
                    "max_drive_time": 0,
                    "max_drive_time_in_seconds": 28800,
                    "max_drive_time_job": 7200,
                    "region": {
                        "h3_index": 617700169958293500,
                        "latitude": 51.05,
                        "longitude": 3.72,
                    },
                    "rules": [
                        {
                            "job_type_limitations": {
                                "Initial Appointment": 10,
                                "Wound Care": 5,
                            },
                            "max_drive_time": 10800,
                            "max_job_complexity": 0,
                            "max_service_time": 21600,
                            "max_work_time": 28800,
                            "min_drive_time": 3600,
                            "min_job_complexity": 0,
                            "min_service_time": 7200,
                            "min_work_time": 14400,
                            "period": {
                                "end": "2007-12-31T17:00:00",
                                "from": parse_datetime("2024-01-01T08:00:00Z"),
                                "to": parse_datetime("2024-01-07T17:00:00Z"),
                            },
                        }
                    ],
                    "start": {
                        "h3_index": 617700169958293500,
                        "latitude": 50.0987624,
                        "longitude": 4.93849204,
                    },
                    "tags": ["plumbing", "electrical"],
                }
            ],
            millis="millis",
            custom_distance_matrices={
                "matrix_service_url": "https://custom-matrix-service.com/api",
                "profile_matrices": {
                    "CAR": {
                        "6": "matrix-car-morning-123",
                        "9": "matrix-car-midday-456",
                        "16": "matrix-car-evening-789",
                    },
                    "TRUCK": {
                        "6": "matrix-truck-morning-abc",
                        "9": "matrix-truck-midday-def",
                    },
                },
            },
            hook="https://example.com",
            label="label",
            options={
                "clustering_threshold_meters": 10000,
                "enable_clustering": False,
                "euclidian": False,
                "explanation": {
                    "enabled": True,
                    "filter_hard_constraints": True,
                    "only_unassigned": True,
                },
                "fair_complexity_per_resource": True,
                "fair_complexity_per_trip": True,
                "fair_workload_per_resource": False,
                "fair_workload_per_trip": False,
                "job_proximity_distance_type": "HAVERSINE",
                "job_proximity_radius": 5000,
                "max_suggestions": 3,
                "minimize_resources": True,
                "only_feasible_suggestions": True,
                "partial_planning": True,
                "polylines": True,
                "routing_engine": "OSM",
                "snap_unit": 300,
                "traffic": 1.1,
                "workload_sensitivity": 0.1,
            },
            relations=[
                {
                    "jobs": ["Job-1", "Job-2"],
                    "time_interval": "FROM_ARRIVAL",
                    "type": "SEQUENCE",
                    "enforce_compatibility": True,
                    "hard_min_wait": True,
                    "max_time_interval": 3600,
                    "max_waiting_time": 1200,
                    "min_time_interval": 0,
                    "partial_planning": False,
                    "resource": "vehicle-1",
                    "tags": ["urgent"],
                    "weight": 1,
                }
            ],
            weights={
                "allowed_resources_weight": 500,
                "asap_weight": 5,
                "clustering_weight": 1,
                "drive_time_weight": 1,
                "job_proximity_weight": 1000,
                "minimize_resources_weight": 0,
                "planned_weight": 1000,
                "priority_weight": 100,
                "ranking_weight": 10,
                "travel_time_weight": 1,
                "urgency_weight": 50,
                "wait_time_weight": 1,
                "workload_spread_weight": 10,
            },
        )
        assert_matches_type(OnRouteResponse, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_sync_solve(self, async_client: AsyncSolviceVrpSolver) -> None:
        response = await async_client.vrp.with_raw_response.sync_solve(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        vrp = await response.parse()
        assert_matches_type(OnRouteResponse, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_sync_solve(self, async_client: AsyncSolviceVrpSolver) -> None:
        async with async_client.vrp.with_streaming_response.sync_solve(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            vrp = await response.parse()
            assert_matches_type(OnRouteResponse, vrp, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_sync_suggest(self, async_client: AsyncSolviceVrpSolver) -> None:
        vrp = await async_client.vrp.sync_suggest(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        )
        assert_matches_type(OnRouteResponse, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_sync_suggest_with_all_params(self, async_client: AsyncSolviceVrpSolver) -> None:
        vrp = await async_client.vrp.sync_suggest(
            jobs=[
                {
                    "name": "Job-1",
                    "allowed_resources": ["string"],
                    "complexity": 1,
                    "disallowed_resources": ["vehicle-3", "vehicle-4"],
                    "duration": 600,
                    "duration_squash": 30,
                    "hard": True,
                    "hard_weight": 1,
                    "initial_arrival": "2023-01-13T09:00:00Z",
                    "initial_resource": "vehicle-1",
                    "job_types": ["Initial Appointment", "Wound Care"],
                    "load": [5, 10],
                    "location": {
                        "h3_index": 617700169958293500,
                        "latitude": 51.0543,
                        "longitude": 3.7174,
                    },
                    "padding": 300,
                    "planned_arrival": "2023-01-13T09:00:00Z",
                    "planned_date": "2023-01-13",
                    "planned_resource": "vehicle-1",
                    "priority": 100,
                    "proficiency": [
                        {
                            "resource": "senior-technician",
                            "duration_modifier": 0.8,
                        }
                    ],
                    "rankings": [
                        {
                            "name": "certified-technician",
                            "ranking": 5,
                        }
                    ],
                    "resumable": True,
                    "tags": [
                        {
                            "name": "plumbing",
                            "hard": False,
                            "weight": 300,
                        }
                    ],
                    "urgency": 80,
                    "windows": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T12:00:00Z",
                            "hard": True,
                            "weight": 1,
                        }
                    ],
                }
            ],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                            "breaks": [{"type": "WINDOWED"}],
                            "end": {
                                "h3_index": 617700169958293500,
                                "latitude": 51.0543,
                                "longitude": 3.7174,
                            },
                            "ignore_travel_time_from_last_job": False,
                            "ignore_travel_time_to_first_job": False,
                            "job_type_limitations": {
                                "Initial Appointment": 2,
                                "Wound Care": 1,
                            },
                            "overtime": {},
                            "overtime_end": "2023-01-13T19:00:00Z",
                            "start": {
                                "h3_index": 617700169958293500,
                                "latitude": 51.0543,
                                "longitude": 3.7174,
                            },
                            "tags": ["delivery", "installation"],
                        }
                    ],
                    "capacity": [500, 200],
                    "category": "CAR",
                    "compatible_resources": ["driver2", "driver3"],
                    "end": {
                        "h3_index": 617700169958293500,
                        "latitude": 50.0987624,
                        "longitude": 4.93849204,
                    },
                    "hourly_cost": 25,
                    "max_drive_distance": 0,
                    "max_drive_time": 0,
                    "max_drive_time_in_seconds": 28800,
                    "max_drive_time_job": 7200,
                    "region": {
                        "h3_index": 617700169958293500,
                        "latitude": 51.05,
                        "longitude": 3.72,
                    },
                    "rules": [
                        {
                            "job_type_limitations": {
                                "Initial Appointment": 10,
                                "Wound Care": 5,
                            },
                            "max_drive_time": 10800,
                            "max_job_complexity": 0,
                            "max_service_time": 21600,
                            "max_work_time": 28800,
                            "min_drive_time": 3600,
                            "min_job_complexity": 0,
                            "min_service_time": 7200,
                            "min_work_time": 14400,
                            "period": {
                                "end": "2007-12-31T17:00:00",
                                "from": parse_datetime("2024-01-01T08:00:00Z"),
                                "to": parse_datetime("2024-01-07T17:00:00Z"),
                            },
                        }
                    ],
                    "start": {
                        "h3_index": 617700169958293500,
                        "latitude": 50.0987624,
                        "longitude": 4.93849204,
                    },
                    "tags": ["plumbing", "electrical"],
                }
            ],
            millis="millis",
            custom_distance_matrices={
                "matrix_service_url": "https://custom-matrix-service.com/api",
                "profile_matrices": {
                    "CAR": {
                        "6": "matrix-car-morning-123",
                        "9": "matrix-car-midday-456",
                        "16": "matrix-car-evening-789",
                    },
                    "TRUCK": {
                        "6": "matrix-truck-morning-abc",
                        "9": "matrix-truck-midday-def",
                    },
                },
            },
            hook="https://example.com",
            label="label",
            options={
                "clustering_threshold_meters": 10000,
                "enable_clustering": False,
                "euclidian": False,
                "explanation": {
                    "enabled": True,
                    "filter_hard_constraints": True,
                    "only_unassigned": True,
                },
                "fair_complexity_per_resource": True,
                "fair_complexity_per_trip": True,
                "fair_workload_per_resource": False,
                "fair_workload_per_trip": False,
                "job_proximity_distance_type": "HAVERSINE",
                "job_proximity_radius": 5000,
                "max_suggestions": 3,
                "minimize_resources": True,
                "only_feasible_suggestions": True,
                "partial_planning": True,
                "polylines": True,
                "routing_engine": "OSM",
                "snap_unit": 300,
                "traffic": 1.1,
                "workload_sensitivity": 0.1,
            },
            relations=[
                {
                    "jobs": ["Job-1", "Job-2"],
                    "time_interval": "FROM_ARRIVAL",
                    "type": "SEQUENCE",
                    "enforce_compatibility": True,
                    "hard_min_wait": True,
                    "max_time_interval": 3600,
                    "max_waiting_time": 1200,
                    "min_time_interval": 0,
                    "partial_planning": False,
                    "resource": "vehicle-1",
                    "tags": ["urgent"],
                    "weight": 1,
                }
            ],
            weights={
                "allowed_resources_weight": 500,
                "asap_weight": 5,
                "clustering_weight": 1,
                "drive_time_weight": 1,
                "job_proximity_weight": 1000,
                "minimize_resources_weight": 0,
                "planned_weight": 1000,
                "priority_weight": 100,
                "ranking_weight": 10,
                "travel_time_weight": 1,
                "urgency_weight": 50,
                "wait_time_weight": 1,
                "workload_spread_weight": 10,
            },
        )
        assert_matches_type(OnRouteResponse, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_sync_suggest(self, async_client: AsyncSolviceVrpSolver) -> None:
        response = await async_client.vrp.with_raw_response.sync_suggest(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        vrp = await response.parse()
        assert_matches_type(OnRouteResponse, vrp, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_sync_suggest(self, async_client: AsyncSolviceVrpSolver) -> None:
        async with async_client.vrp.with_streaming_response.sync_suggest(
            jobs=[{"name": "Job-1"}],
            resources=[
                {
                    "name": "vehicle-1",
                    "shifts": [
                        {
                            "from": "2023-01-13T08:00:00Z",
                            "to": "2023-01-13T17:00:00Z",
                        }
                    ],
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            vrp = await response.parse()
            assert_matches_type(OnRouteResponse, vrp, path=["response"])

        assert cast(Any, response.is_closed) is True
