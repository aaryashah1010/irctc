# AWS Cost Estimation

**Group:** 40  
**Course:** IT457 — Cloud Computing  
**Date:** Nov 2026

## Deployment Configuration

| Component | Instance Type | Quantity | Hours/Month |
|---|---|---|---|
| Application Load Balancer | ALB | 1 | 730 |
| EC2 (Auto Scaling group) | t3.small | 1–6 | 730 (max) |
| RDS PostgreSQL | db.t3.medium | 1 | 730 |
| Load generator | c6i.xlarge | 1 | 730 (test duration only) |

## Estimated Monthly Cost (ap-south-1, Mumbai)

| Component | Unit Cost (USD/hr) | Monthly Cost (USD) | Notes |
|---|---|---|---|
| Application Load Balancer | ~0.0225 | ~16.43 | ALB-hour + LCU |
| EC2 t3.small | ~0.0208 | ~15.18 | 1 instance baseline |
| EC2 t3.small (6 max) | ~0.0208 | ~91.08 | 6 instances peak |
| RDS db.t3.medium | ~0.043 | ~31.39 | Single AZ, no Multi-AZ |
| Load generator c6i.xlarge | ~0.17 | ~124.10 | Test duration only |
| Data transfer | Variable | — | First 100 GB free/month |

## Total Estimated Range

- **Baseline (1 instance):** ~$63–$80/month
- **Peak (6 instances):** ~$140–$160/month
- **Load generator (during tests only):** ~$124/month (if run continuously)

## Notes

- These are ap-south-1 (Mumbai) list prices as of Nov 2026.
- Actual costs vary with usage, data transfer, and reserved instance discounts.
- RDS storage, snapshot, and backup costs are not included.
- ALB LCU charges depend on active connections and processed bytes.
- AWS compute was shut down after experiments; recurring cost is $0 unless redeployed.
