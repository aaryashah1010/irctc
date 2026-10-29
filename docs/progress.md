# Project Progress — IT457 Group 40 (IRCTC Cloud Scaling)

**Team:** Aarya Shah (202301036), Visha Sitapara (202301414), Krish Dhola (202301189)

## Weekly Status

| Week | Deliverable | Status | Owner | Notes |
|---|---|---|---|---|
| Week 1 | One-page summary, research notes, source list | Done | All | Docs in `docs/` |
| Week 2 | Case report (10 pages), diagrams | Done | All | `week2/report/`, `week2/diagrams/` |
| Week 3 | Booking API, AWS deployment, load-test experiments | Done | All | `week3/` |

## Open Items

From `week2/README.md` Section "Open items before submission":

- [x] Roles in Section 10 discussed and agreed among the three members.
- [x] Choose the cloud provider and region — AWS ALB + Auto Scaling group in ap-south-1 (Mumbai).
- [ ] Re-read the report against the references; check every number once more.
- [ ] Regenerate `docs/Group40.pdf`, which still has the old "65%" wording.
- [ ] Look for CRIS or ITI procurement documents on the new PRS (not found yet).
- [x] Log this week's work in the progress document.

## Roles (from week2/report/report.md Section 10)

Agreed among all three members. Each member contributed to research, documentation, code, and experiments across the three weeks.

## AWS Resources

All AWS infrastructure (EC2, ALB, RDS) was torn down after Week 3 experiments to avoid ongoing costs. Infrastructure can be redeployed via `week3/aws/` scripts.

## Notes

- All experiment results are from our own synthetic workload; they are not IRCTC production figures.
- One run per experiment setting; small differences between configurations are within noise.
- The load-shedding experiment (R5) remained inconclusive at the end of Week 3.
