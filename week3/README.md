# Week 3: IRCTC Booking API on AWS

Local FastAPI booking API with PostgreSQL, containerized with Docker, deployed to AWS behind an ALB with Auto Scaling, and load-tested with Locust.

## Contents

| Path | What it is |
|---|---|
| `app/main.py` | FastAPI booking API (`/health`, `/availability`, `/book`) |
| `app/database.py` | PostgreSQL connection pool and queries |
| `app/__init__.py` | Package marker |
| `Dockerfile` | Container image for the API |
| `docker-compose.yml` | Local run with API + PostgreSQL |
| `requirements.txt` | Python dependencies |
| `tests/test_bookings.py` | Correctness tests (pytest + httpx) |
| `tests/conftest.py` | Test fixtures (API client, DB reset) |
| `load_tests/locustfile.py` | Locust load test |
| `load_tests/correctness_aws.py` | Correctness checks against AWS deployment |
| `load_tests/shapes/ramp.py` | Ramp load shape |
| `load_tests/shapes/burst.py` | Burst load shape |
| `load_tests/results/aws/` | Raw Locust results per experiment |
| `aws/` | Infrastructure and experiment shell scripts |
| `analysis/collect_metrics.py` | Metric collection from results |
| `analysis/make_charts.py` | Summary charts |
| `analysis/make_charts_extra.py` | Additional charts |
| `report/aws_experiments.md` | Full AWS experiment write-up |
| `report/implementation_and_testing.md` | Local phase handover |
| `report/figures/` | Summary charts (PNG) |
| `test_screenshots/` | API test result screenshots |

## API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Health check |
| `/availability` | GET | Available seats for a train |
| `/book` | POST | Book seats (updates inventory) |

## Local Run (Docker)

```bash
cd week3
docker-compose up --build
```

API is available at `http://localhost:8000`.

Run correctness tests:

```bash
pip install -r requirements.txt
pytest tests/
```

## AWS Deployment

Deploy using the scripts in `week3/aws/`:

```bash
cd week3/aws
./01-infra.sh      # Create VPC, ALB, ASG, RDS
./02-image.sh      # Build and push Docker image to ECR
./03-app.sh        # Deploy application to ASG
```

Then run load tests against the ALB DNS name:

```bash
cd week3
locust -f load_tests/locustfile.py --host=http://<ALB-DNS>
```

Open the Locust web UI at `http://localhost:8089`.

Tear down when done:

```bash
cd week3/aws
./teardown.sh
```

## Load Shapes

- **`ramp.py`** — linearly increasing user count
- **`burst.py`** — sudden spike to simulate Tatkal window

Use with Locust:

```bash
locust -f load_tests/locustfile.py --shape burst --host=http://<ALB-DNS>
```

## Results

Experiment results (Locust CSVs, logs, meta JSON) are under `load_tests/results/aws/`. Summary charts are in `report/figures/`. The full experiment narrative is in `report/aws_experiments.md`.

## Note

AWS compute was shut down after experiments. Infrastructure must be redeployed via `week3/aws/` scripts to reproduce results.
