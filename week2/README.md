# Week 2: Case analysis and report

Deliverable (from the IT457 project plan): a 10-page report on the study, the exercise plan and the roles of team members.

## Contents

| Path | What it is |
|---|---|
| `report/report.md` | Report source (edit this) |
| `report/Week2_Report_Group40.docx`, `.pdf` | Built report (9 pages) |
| `diagrams/make_diagrams.py` | Generates Figures 1 to 3 as PNG |
| `diagrams/*.png` | Case architecture, exercise architecture, capacity chart |
| `tools/build_report.js` | Builds the docx from `report.md` |

## Rebuild

```bash
python week2/diagrams/make_diagrams.py
NODE_PATH=<folder containing node_modules/docx> node week2/tools/build_report.js
```

The PDF is exported from the docx with Word (File > Export), or LibreOffice if installed.

## Open items before submission

- [x] Roles in Section 10 discussed and agreed among the three members.
- [ ] Choose the cloud provider and region (Section 9 proposes AWS ALB + Auto Scaling group).
- [ ] Re-read the report against the references; check every number once more.
- [ ] Regenerate `docs/Group40.pdf`, which still has the old "65%" wording.
- [ ] Look for CRIS or ITI procurement documents on the new PRS (not found yet).
- [ ] Log this week's work in the progress document.
