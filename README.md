# IRCTC Cloud Scaling — IT457 Group 40

Proof-of-concept for scaling a railway booking system under Tatkal-like burst load. This repo documents a booking API, containerization, AWS deployment scripts, Locust load tests, and experiment results across three project weeks.

## Team

| Member | Roll Number |
|---|---|
| Aarya Shah | 202301036 |
| Visha Sitapara | 202301414 |
| Krish Dhola | 202301189 |

## Repository Layout

| Path | What it is |
|---|---|
| `week2/` | Case analysis, report source, diagrams, report builder |
| `week3/` | FastAPI booking API, PostgreSQL, Docker, AWS deployment scripts, Locust load tests, results, charts |
| `docs/` | Week summaries, research notes, final report PDF |

## Tech Stack

- **API:** FastAPI (Python)
- **Database:** PostgreSQL
- **Containerization:** Docker + docker-compose
- **Load testing:** Locust
- **Cloud:** AWS (EC2, ALB, Auto Scaling)
- **Charts:** Matplotlib (Python)

## Quick Start

### Local (Docker)

```bash
cd week3
docker-compose up --build
```

The booking API runs on `http://localhost:8000`. Run the correctness tests:

```bash
cd week3
pip install -r requirements.txt
pytest tests/
```

### AWS Deployment

Deploy to AWS using the scripts in `week3/aws/`:

```bash
cd week3/aws
./01-infra.sh
./02-image.sh
./03-app.sh
```

See `week3/aws/README.md` for the full deployment flow and experiment scripts.

## Running Load Tests

```bash
cd week3
locust -f load_tests/locustfile.py --host=http://<ALB-DNS>
```

Open the Locust web UI at `http://localhost:8089` and configure users/spawn rate.

## Results

Experiment results (Locust stats, charts, meta JSON) are stored under `week3/load_tests/results/aws/`. Summary charts are in `week3/report/figures/`.

## Deliverables by Week

| Week | Deliverable | Location |
|---|---|---|
| Week 1 | One-page summary, research notes, source list | `docs/` |
| Week 2 | Case report (10 pages), diagrams | `week2/report/`, `week2/diagrams/` |
| Week 3 | Booking API, AWS deployment, load-test experiments | `week3/` |

## License

See `LICENSE`.
