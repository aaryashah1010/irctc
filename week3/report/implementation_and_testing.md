# IRCTC Cloud Scaling Project
## Development Progress & AWS Handover Document

**Course:** IT457 — Cloud Computing  
**Project theme:** Scalability & High-Traffic Events  
**Case study:** IRCTC-style railway ticket booking system  
**Repository:** https://github.com/aaryashah1010/irctc  
**Current stage:** Local implementation and AWS scaling experiments completed; AWS compute has been shut down, and one load-shedding experiment remains inconclusive

---

## 1. Project Overview

IRCTC experiences large traffic spikes when railway tickets become available, particularly during high-demand booking periods such as Tatkal reservations.

A system handling this traffic needs to respond quickly, maintain correct seat availability, and prevent multiple users from booking the same seat.

Our project builds a simplified railway booking application to investigate how cloud infrastructure can help handle increasing traffic.

**Our main objectives are to:**

- Build a working railway booking API.
- Maintain correct seat inventory during simultaneous booking requests.
- Measure application performance under increasing simulated traffic.
- Deploy the application on AWS and investigate horizontal scaling and load balancing.
- Compare performance and resource usage under different deployment configurations.

**Scope clarification:** This is an educational simulation inspired by railway booking systems. We are not reproducing IRCTC's internal production architecture or claiming that our local performance represents actual IRCTC capacity.

---

## 2. Work Completed So Far

### 2.1 Backend API

We implemented a REST API using FastAPI and Python.

The application currently supports three endpoints:

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Checks whether the API is responding |
| `/availability` | GET | Retrieves available seats for a train |
| `/book` | POST | Books seats and updates inventory |

The API includes input validation and returns appropriate HTTP errors for cases such as an unknown train or insufficient seats.

### 2.2 PostgreSQL database

PostgreSQL stores the train inventory and booking records.

Two tables have been created:

**`train_inventory`**

Stores each train's ID, total seats, and currently available seats.

**`bookings`**

Stores the booking ID, train ID, passenger name, number of seats booked, and booking timestamp.

The database includes constraints to prevent invalid seat counts and references bookings to existing trains.

The initial application data contains train ID `12951` with 100 seats.

### 2.3 Concurrent booking correctness

A key requirement is preventing overbooking when several users try to book seats simultaneously.

The booking operation uses a conditional SQL `UPDATE` that reduces available seats only when enough seats remain. This operation is atomic at the database level.

An automated concurrency test sends 20 simultaneous requests to book one seat each for a test train containing only 10 seats.

**Expected and observed result:**

- 10 successful bookings.
- 10 rejected bookings.
- 0 seats remaining.
- Exactly 10 booking records.

This test passed, demonstrating that the current implementation prevents overselling in this scenario.

### 2.4 Docker containerization

The application runs locally using Docker Compose.

The setup includes:

- A FastAPI application container.
- A PostgreSQL database container.
- A persistent Docker volume for PostgreSQL data.
- A database health check and API startup dependency.

The API is exposed on port `8000`, while PostgreSQL is mapped to port `5432` for local development and testing.

The API and database communicate through Docker Compose's internal network when running in containers.

### 2.5 Automated tests

We created automated tests using `pytest` and `httpx`.

The current tests verify:

1. The health endpoint returns a successful response.
2. Concurrent booking requests do not oversell the test train.

**Latest recorded result:** 2 tests passed.

### 2.6 Load testing using Locust

We used Locust to simulate concurrent users making API requests.

The initial workload is read-oriented:

- 90% availability requests.
- 10% health-check requests.

*Update:* the workload in `load_tests/locustfile.py` now sends 90% availability and 10% booking requests, so the results below (recorded with the earlier read-only mix) must not be compared directly with new runs.

These percentages are a modelling assumption for our experiment, not measured statistics from real IRCTC traffic.

The load tests helped us establish an initial local performance baseline.

---

## 3. Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| Backend framework | FastAPI |
| Database | PostgreSQL |
| Database driver | Psycopg |
| Input validation | Pydantic |
| Containerization | Docker |
| Container orchestration | Docker Compose |
| Automated testing | pytest, httpx |
| Load testing | Locust |
| Development environment | Windows, VS Code, PowerShell |
| Version control | Git and GitHub |

---

## 4. Repository Structure

The main implementation is located in the `week3` directory.

```text
irctc/
├── docs/
├── week2/
└── week3/
    ├── app/
    │   ├── __init__.py
    │   ├── database.py
    │   └── main.py
    ├── tests/
    │   ├── conftest.py
    │   └── test_bookings.py
    ├── load_tests/
    │   ├── locustfile.py
    │   └── shapes/
    │       ├── ramp.py
    │       └── burst.py
    ├── Dockerfile
    ├── docker-compose.yml
    └── requirements.txt
```

**Important files:**

- `app/main.py` — API endpoints and booking logic.
- `app/database.py` — Database connection and table initialization.
- `tests/test_bookings.py` — Health and concurrent-booking correctness tests.
- `tests/conftest.py` — Configures the Python import path for tests.
- `load_tests/locustfile.py` — Simulated user workload (availability and booking requests).
- `load_tests/shapes/ramp.py` and `burst.py` — Ramp and Tatkal-style burst load profiles.
- `Dockerfile` — Builds the API image.
- `docker-compose.yml` — Configures the API and PostgreSQL services.
- `requirements.txt` — Python dependencies.

The `docs`, `week2`, and `load_tests` directories may contain additional project material; inspect them directly for the latest contents.

---

## 5. How to Run the Project Locally

### Prerequisites

Install Python, Git, Docker Desktop, and VS Code.

Clone the repository if it is not already available:

```powershell
git clone https://github.com/aaryashah1010/irctc.git
cd irctc
```

### Step 1: Start the application

From the repository root:

```powershell
docker compose -f week3/docker-compose.yml up --build -d
```

Check the container status:

```powershell
docker compose -f week3/docker-compose.yml ps
```

View API logs if needed:

```powershell
docker compose -f week3/docker-compose.yml logs api
```

Open the interactive API documentation:

`http://localhost:8000/docs`

The documentation allows the endpoints to be tested manually.

### Step 2: Run automated tests

Activate the existing virtual environment, or create one if necessary:

```powershell
python -m venv week3/.venv
```

Activate it:

```powershell
.\week3\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r week3/requirements.txt
```

Run the tests:

```powershell
python -m pytest week3/tests/test_bookings.py -v
```

**Important:** Run the tests while the Dockerized PostgreSQL database and API are running. The tests connect to the local database port and send HTTP requests to the API.

The test fixture creates and cleans up a separate test train with ID `99001`.

### Step 3: Run Locust

With the Dockerized application running, execute:

```powershell
python -m locust -f week3/load_tests/locustfile.py --host http://127.0.0.1:8000
```

To run a scripted load profile instead of setting users by hand, add a shape file. Set the peak with `LOCUST_PEAK_USERS` (default 200):

```powershell
# Ramp: warm-up, steady ramp, cool-down
python -m locust -f week3/load_tests/locustfile.py,week3/load_tests/shapes/ramp.py --host http://127.0.0.1:8000

# Tatkal-style burst: quiet, jump to peak in about 10 s, hold, drop
python -m locust -f week3/load_tests/locustfile.py,week3/load_tests/shapes/burst.py --host http://127.0.0.1:8000
```

Bookings in the load test go to train `12952`, which is seeded with 1,000,000 seats so a run does not sell out.

Open:

`http://localhost:8089`

Configure the number of users and spawn rate, start the test, and observe the Statistics and Charts tabs.

### Step 4: Monitor Docker resources

In a separate PowerShell terminal:

```powershell
docker stats
```

This displays live CPU and memory usage for the API and database containers.

Stop the display with `Ctrl+C`.

### Step 5: Stop the application

```powershell
docker compose -f week3/docker-compose.yml down
```

This stops and removes the containers but preserves the named PostgreSQL data volume.

To remove the database volume as well, use `docker compose down -v` only when the stored data is no longer needed.

---

## 6. Local Load-Test Results

The following results were recorded from Locust screenshots during initial experiments.

The workload was predominantly read-oriented, using availability and health-check requests.

| Configured users | Requests/sec | Median latency | P95 latency | P99 latency | Failed requests |
|---:|---:|---:|---:|---:|---:|
| 20 | 12.9 | 14 ms | 23 ms | 27 ms | 0 |
| 50 | 32.3 | 14 ms | 23 ms | 32 ms | 0 |
| 100 | 66.6 | 13 ms | 33 ms | 55 ms | 0 |
| 200 — Run 1 | 132.2 | 15 ms | 46 ms | 97 ms | 0 |
| 200 — Run 2 | 130.5 | 16 ms | 49 ms | 100 ms | 0 |

The two 200-user runs produced slightly different results, as expected in performance testing.

### Observations

1. Throughput increased as the configured user count increased.
2. Median response time remained relatively low during these experiments.
3. P95 and P99 latency increased under heavier load, indicating that some requests took longer.
4. No failed requests were recorded in these runs.
5. During one 200-user run, a snapshot of Docker resource usage showed approximately 88.58% CPU for the API container and 59.50% for PostgreSQL.
6. Memory usage in that snapshot was approximately 49 MiB for the API and 39 MiB for PostgreSQL.

### Limitations

- The exact duration of every recorded run was not independently documented, so total request counts should not be directly compared across runs.
- The CPU figures are a single snapshot, not peak or average utilization measurements.
- Locust, the API, and PostgreSQL share the same computer, so local performance may be limited by the load generator or host machine.
- The workload does not yet reproduce a realistic booking spike involving substantial write traffic.
- These results are not a measure of production IRCTC capacity.

The measurements should therefore be treated as an initial development baseline, not a definitive capacity benchmark.

---

## 7. Current Architecture

The project has both a local Docker Compose setup and an AWS experimental
deployment. Locally, the application follows this architecture:

```text
Locust / API client
        |
        v
FastAPI application
        |
        v
PostgreSQL database
```

Docker Compose manages the local application and database containers. The AWS
deployment and measured results are documented in
[`aws_experiments.md`](aws_experiments.md).

### AWS experimental architecture

```text
Locust load generator
        |
        v
Application Load Balancer
        |
        v
EC2 Auto Scaling Group
   |             |
   v             v
API Instance 1  API Instance 2
   |             |
   +------|------+
          |
          v
Amazon RDS
for PostgreSQL
```

The AWS experiment used an Application Load Balancer, an EC2 Auto Scaling Group,
Amazon RDS for PostgreSQL, and CloudWatch metrics. Fixed-capacity, ramp, burst,
scheduled pre-scaling, correctness, instance-failure, and load-shedding runs were
collected. See [`aws_experiments.md`](aws_experiments.md) for configuration,
results, limitations, and figures.

### Important technical considerations

- The API must be stateless across instances.
- All instances must use the same database.
- Seat inventory updates must remain atomic.
- Database connection limits must be considered when adding API instances.
- Secrets and credentials must be handled securely rather than embedded as production configuration.
- AWS experiments should use controlled workloads and include cost monitoring.
- Local and AWS results should only be compared when the workload and measurement conditions are sufficiently similar.

---

## 8. Handover Checklist

- [x] FastAPI booking API implemented.
- [x] PostgreSQL schema and initial train inventory created.
- [x] Docker Compose setup working locally.
- [x] Automated correctness tests passing.
- [x] Initial Locust tests completed.
- [x] Initial CPU and memory observations collected.
- [x] Code pushed to GitHub.
- [x] Local performance results documented.
- [x] AWS architecture and experimental cost estimate documented.
- [x] AWS application and database deployed for the experiments.
- [x] Load balancer and autoscaling configured.
- [x] CloudWatch metrics collected for the experiments.
- [x] AWS load tests and comparison documented in [`aws_experiments.md`](aws_experiments.md).
- [x] Experimental conclusions and limitations documented.
- [ ] Re-run or correct the load-shedding experiment; the saved R5 run produced no 429 responses.
- [x] Shut down AWS compute and services; preserve the RDS snapshot and S3 experiment results.

## 9. Final Summary

The local phase has produced a working, containerized railway booking API with a PostgreSQL backend, automated tests for concurrent booking correctness, and initial Locust performance measurements.

The AWS phase evaluated horizontal scaling, hot-train contention, ramp and burst
traffic, scheduled capacity, correctness, and instance failure. The saved results
show that spreading bookings scales better than concentrating them on one train,
pre-scaling gave lower burst latency than reactive scaling, and the failure test
had a short load-balancer 5xx window while preserving database consistency. The
R5 shedding result is inconclusive because it produced no 429 responses.

**Current status (14 November 2026):** Implementation and experiment analysis
are documented. The AWS CLI was verified, the live deployment was checked, then
its compute and services were shut down. The final RDS snapshot and S3 experiment
results were retained. The load-shedding experiment still needs a corrected
rerun; see [`aws_experiments.md`](aws_experiments.md) for the shutdown record.
