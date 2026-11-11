# Load-Shedding Experiment R5 — Rerun Plan

**Group:** 40  
**Course:** IT457 — Cloud Computing  
**Date:** Nov 2026  
**Status:** Inconclusive — rerun required

## Background

`week3/report/aws_experiments.md` documents the Week 3 AWS experiments. The load-shedding experiment (R5) was attempted but did not produce conclusive results. This document outlines the rerun plan.

## What R5 Should Test

- Shed excess load when instance count hits the Auto Scaling group maximum (6 instances).
- Verify that the API returns appropriate HTTP responses (e.g., 429 Too Many Requests or 503 Service Unavailable) for requests beyond capacity, rather than failing silently or timing out.
- Measure whether load shedding protects the database from overload during a burst.

## Rerun Procedure

1. Deploy infrastructure via `week3/aws/01-infra.sh`.
2. Build and push the Docker image via `week3/aws/02-image.sh`.
3. Deploy the application via `week3/aws/03-app.sh`.
4. Reset the database before the run via `week3/aws/reset-data.sh`.
5. Generate a burst load using `load_tests/shapes/burst.py` targeting the ALB DNS.
6. Monitor instance count, database CPU, and response codes.
7. Verify that shed requests return 429/503 and that booked/sold-out responses remain correct (`201`/`409`).
8. Tear down via `week3/aws/teardown.sh`.

## Expected Outcome

- At 6 instances, additional users beyond capacity receive shed responses (429/503).
- Database CPU stays within safe limits during the burst.
- Booked and sold-out counts remain consistent with the database inventory.

## Files Involved

- `week3/aws/01-infra.sh`, `03-app.sh`, `reset-data.sh`, `teardown.sh`
- `week3/load_tests/shapes/burst.py`
- `week3/load_tests/locustfile.py`
- `week3/report/aws_experiments.md`
