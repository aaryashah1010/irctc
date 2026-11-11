# Week 3 Results Summary

**Group:** 40  
**Course:** IT457 — Cloud Computing  
**Status:** Complete (AWS resources torn down)

## Deployment

| Component | Configuration |
|---|---|
| Region | ap-south-1 (Mumbai) |
| Load balancer | Application Load Balancer, HTTP :80, `/health` check |
| Compute | Auto Scaling group, min 1 / max 6, `t3.small` |
| Scaling | Target tracking on average CPU, target 50% |
| Application | Docker image from ECR, 2 uvicorn workers, connection pool of 8 |
| Database | Amazon RDS PostgreSQL 17, `db.t3.medium`, single AZ |
| Load generator | `c6i.xlarge`, Locust with 4 processes |

## Experiments

### Fixed capacity (A and B)
- 1,500 users for 3 minutes at 1, 2, 3, 4, 6 instances (autoscaling off)
- **A (spread):** bookings across 200 trains
- **B (hot train):** every booking to one train

### Burst (R3 and R4)
- 10 users → jump to 1,200 users in ~10 s → hold 5 minutes → back to 10
- **R3 (reactive):** starts at 1 instance, relies on CPU scaling
- **R4 (pre-scaled):** starts at 4 instances before the window

## Key Findings

- Response time improves with instance count up to a point; database CPU becomes the bottleneck.
- Pre-scaling (R4) absorbed the initial burst better than reactive scaling (R3).
- Connection pool and advisory lock prevented race conditions during concurrent bookings.
- One run per setting; small differences are within noise.
- Load-shedding experiment (R5) remained inconclusive.

## Deliverables

- `week3/app/` — FastAPI booking API with PostgreSQL
- `week3/Dockerfile`, `docker-compose.yml` — Containerization
- `week3/tests/` — Correctness tests (pytest + httpx)
- `week3/load_tests/` — Locust load tests and shapes
- `week3/aws/` — Infrastructure and experiment scripts
- `week3/load_tests/results/aws/` — Raw Locust results
- `week3/report/figures/` — Summary charts
- `week3/report/aws_experiments.md` — Full experiment write-up
