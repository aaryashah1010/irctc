# Week 3 Summary: AWS Deployment and Load-Test Experiments

**Group:** 40  
**Course:** IT457 — Cloud Computing  
**Date:** Oct 2026  
**Status:** Complete (AWS resources torn down after experiments)

## Overview

Week 3 extended the local FastAPI booking API into a cloud deployment on AWS behind an Application Load Balancer with Auto Scaling. The same booking workload was then load-tested from inside the AWS region using Locust, and results were recorded across fixed-capacity and burst experiments.

## What Was Deployed

| Component | Configuration |
|---|---|
| Region | ap-south-1 (Mumbai), default VPC, 3 AZs |
| Load balancer | Application Load Balancer, HTTP :80, `/health` check every 15 s |
| Compute | Auto Scaling group, min 1 / max 6, `t3.small` (2 vCPU) |
| Scaling rule | Target tracking on average CPU, target 50% |
| Application | Docker image from ECR, 2 uvicorn workers per instance, connection pool of 8 per worker |
| Database | Amazon RDS PostgreSQL 17, `db.t3.medium`, single AZ, not public |
| Load generator | `c6i.xlarge` in same region, Locust with 4 processes |

Application changes for the cloud phase:
- Database connection pool
- Configurable worker count
- Advisory lock to prevent table-creation races across workers/instances
- 75-second keep-alive

All infrastructure is created and removed by scripts in `week3/aws/`.

## Experiments

### Fixed capacity (A and B)
- 1,500 simulated users for 3 minutes
- Exactly 1, 2, 3, 4, and 6 instances (autoscaling off)
- Database reset before each run
- **A (spread):** bookings across 200 trains
- **B (hot train):** every booking to one train

### Burst (R3 and R4)
- 10 users for 60 s → jump to 1,200 users in ~10 s → hold 5 minutes → back to 10
- Bookings spread over 200 trains
- **R3 (reactive):** starts at 1 instance, relies on CPU scaling rule
- **R4 (pre-scaled):** starts at 4 instances (capacity added before the window)

### Correctness
- `201` (booked) and `409` (sold out) both count as valid
- Any other status counts as failure

## Key Findings

- Response time and throughput improve with instance count up to a point; database CPU becomes the bottleneck at higher instance counts.
- Reactive autoscaling (R3) took time to scale up during the burst; pre-scaling (R4) absorbed the initial spike better.
- Connection pool and advisory lock prevented race conditions during concurrent booking attempts.
- One run per setting only, so small differences between configurations are within noise.
- The load-shedding experiment (R5) remained inconclusive at the end of Week 3.

## Deliverables

| File | Description |
|---|---|
| `week3/app/main.py` | FastAPI booking API |
| `week3/app/database.py` | PostgreSQL connection pool and queries |
| `week3/Dockerfile`, `docker-compose.yml` | Containerization |
| `week3/tests/test_bookings.py` | Correctness tests |
| `week3/load_tests/locustfile.py` | Locust load test |
| `week3/aws/*.sh` | Infrastructure and experiment scripts |
| `week3/load_tests/results/aws/` | Raw Locust results |
| `week3/report/figures/` | Summary charts |
| `week3/report/aws_experiments.md` | Full experiment write-up |
| `week3/report/implementation_and_testing.md` | Local phase handover |

## Limitations

- Results are from our own deployment and a synthetic workload; they are not IRCTC figures.
- AWS compute was shut down after experiments; infrastructure must be redeployed via `week3/aws/` scripts to reproduce.
- One run per setting limits statistical confidence.
