# AWS deployment scripts

Scripts that deploy the Week 3 booking API on AWS (ap-south-1) and run the load
tests. Run them from the repository root in Git Bash with the AWS CLI configured.
Never commit `.env.aws` (database password) or `.tmp/`; both are git-ignored.

| Script | What it does | Billing starts |
|---|---|---|
| `01-infra.sh` | ECR repository, security groups, instance role, RDS database | database |
| `02-image.sh` | builds `week3/Dockerfile` and pushes it to ECR (needs Docker Desktop) | no |
| `03-app.sh` | launch template, target group, load balancer, Auto Scaling group | ALB, instances |
| `04-loadgen.sh` | load-generator instance and a private S3 bucket for results | instance |
| `status.sh` | shows instances, target health, database and the URL | no |
| `set-capacity.sh N` | pins the group to N instances; `auto` restores 1 to 6 | no |
| `reset-data.sh` | empties bookings and refills the demo trains | no |
| `run-test.sh` | runs one Locust test from the load generator and downloads results | no |
| `sweep.sh` | the same load at 1, 2, 3, 4, 6 instances | no |
| `burst-experiment.sh` | Tatkal-style burst, reactive and pre-scaled | no |
| `teardown.sh` | deletes everything that costs money | stops billing |

Approximate cost while everything runs: $0.5 to $0.7 per hour (database $0.106,
load generator $0.17, load balancer $0.024, instances $0.0224 each).

**Always run `bash week3/aws/teardown.sh` when you finish a session.**
Use `--keep-db` to keep the database and `--all` to also remove the security
groups, role, bucket and ECR repository.

Settings can be overridden through environment variables (see `common.sh`), for
example `INSTANCE_TYPE`, `DB_CLASS`, `UVICORN_WORKERS`, `DB_POOL_MAX_SIZE`,
`ASG_MAX`. The report section is `week3/report/aws_experiments.md`.
