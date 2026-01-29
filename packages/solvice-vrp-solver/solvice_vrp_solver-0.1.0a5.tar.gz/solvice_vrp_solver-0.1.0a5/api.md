# Vrp

Types:

```python
from solvice_vrp_solver.types import (
    CustomDistanceMatrices,
    ExplanationOptions,
    Job,
    Location,
    Message,
    Options,
    Period,
    Relation,
    RelationType,
    Request,
    Resource,
    Rule,
    Shift,
    Weights,
    Window,
)
```

Methods:

- <code title="get /v2/vrp/demo">client.vrp.<a href="./src/solvice_vrp_solver/resources/vrp/vrp.py">demo</a>(\*\*<a href="src/solvice_vrp_solver/types/vrp_demo_params.py">params</a>) -> <a href="./src/solvice_vrp_solver/types/request.py">Request</a></code>
- <code title="post /v2/vrp/evaluate">client.vrp.<a href="./src/solvice_vrp_solver/resources/vrp/vrp.py">evaluate</a>(\*\*<a href="src/solvice_vrp_solver/types/vrp_evaluate_params.py">params</a>) -> <a href="./src/solvice_vrp_solver/types/vrp/solvice_status_job.py">SolviceStatusJob</a></code>
- <code title="post /v2/vrp/solve">client.vrp.<a href="./src/solvice_vrp_solver/resources/vrp/vrp.py">solve</a>(\*\*<a href="src/solvice_vrp_solver/types/vrp_solve_params.py">params</a>) -> <a href="./src/solvice_vrp_solver/types/vrp/solvice_status_job.py">SolviceStatusJob</a></code>
- <code title="post /v2/vrp/suggest">client.vrp.<a href="./src/solvice_vrp_solver/resources/vrp/vrp.py">suggest</a>(\*\*<a href="src/solvice_vrp_solver/types/vrp_suggest_params.py">params</a>) -> <a href="./src/solvice_vrp_solver/types/vrp/solvice_status_job.py">SolviceStatusJob</a></code>
- <code title="post /v2/vrp/sync/evaluate">client.vrp.<a href="./src/solvice_vrp_solver/resources/vrp/vrp.py">sync_evaluate</a>(\*\*<a href="src/solvice_vrp_solver/types/vrp_sync_evaluate_params.py">params</a>) -> <a href="./src/solvice_vrp_solver/types/vrp/on_route_response.py">OnRouteResponse</a></code>
- <code title="post /v2/vrp/sync/solve">client.vrp.<a href="./src/solvice_vrp_solver/resources/vrp/vrp.py">sync_solve</a>(\*\*<a href="src/solvice_vrp_solver/types/vrp_sync_solve_params.py">params</a>) -> <a href="./src/solvice_vrp_solver/types/vrp/on_route_response.py">OnRouteResponse</a></code>
- <code title="post /v2/vrp/sync/suggest">client.vrp.<a href="./src/solvice_vrp_solver/resources/vrp/vrp.py">sync_suggest</a>(\*\*<a href="src/solvice_vrp_solver/types/vrp_sync_suggest_params.py">params</a>) -> <a href="./src/solvice_vrp_solver/types/vrp/on_route_response.py">OnRouteResponse</a></code>

## Jobs

Types:

```python
from solvice_vrp_solver.types.vrp import (
    OnRouteResponse,
    OnrouteConstraint,
    Score,
    SolviceStatusJob,
    Unresolved,
    Visit,
    JobExplanationResponse,
)
```

Methods:

- <code title="get /v2/vrp/jobs/{id}">client.vrp.jobs.<a href="./src/solvice_vrp_solver/resources/vrp/jobs.py">retrieve</a>(id) -> <a href="./src/solvice_vrp_solver/types/request.py">Request</a></code>
- <code title="get /v2/vrp/jobs/{id}/explanation">client.vrp.jobs.<a href="./src/solvice_vrp_solver/resources/vrp/jobs.py">explanation</a>(id) -> <a href="./src/solvice_vrp_solver/types/vrp/job_explanation_response.py">JobExplanationResponse</a></code>
- <code title="get /v2/vrp/jobs/{id}/solution">client.vrp.jobs.<a href="./src/solvice_vrp_solver/resources/vrp/jobs.py">solution</a>(id) -> <a href="./src/solvice_vrp_solver/types/vrp/on_route_response.py">OnRouteResponse</a></code>
- <code title="get /v2/vrp/jobs/{id}/status">client.vrp.jobs.<a href="./src/solvice_vrp_solver/resources/vrp/jobs.py">status</a>(id) -> <a href="./src/solvice_vrp_solver/types/vrp/solvice_status_job.py">SolviceStatusJob</a></code>
