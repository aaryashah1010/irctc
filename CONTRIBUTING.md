# Contributing

Guidelines for contributing to the IRCTC Cloud Scaling project (IT457, Group 40).

## Before You Start

- All three team members (Aarya Shah, Visha Sitapara, Krish Dhola) have agreed roles in `week2/report/report.md` Section 10.
- Discuss significant changes with the team before implementing.

## Commit Conventions

Use conventional commit messages:

```
<type>: <short description>
```

Types:
- `docs` — documentation changes (README, reports, notes)
- `feat` — new feature (API endpoint, script, experiment)
- `fix` — bug fix
- `test` — adding or modifying tests
- `refactor` — code restructure without behavior change
- `chore` — maintenance (config, dependencies, CI)

Examples:

```
docs: add Week 3 summary report
feat: add burst load shape script
fix: correct Week 1 Tatkal statistic
test: add booking correctness tests
```

## Making a Change

1. Create a branch from `main`:

   ```bash
   git checkout -b feature/your-change
   ```

2. Make your changes and stage them:

   ```bash
   git add <your files>
   ```

3. Commit with a descriptive message:

   ```bash
   git commit -m "docs: add project README"
   ```

4. Push your branch:

   ```bash
   git push origin feature/your-change
   ```

5. Open a pull request and tag the other team members for review.

## Reporting Issues

If you find a bug in the API, a problem with the AWS scripts, or an inconsistency in results, open an issue and assign the relevant team member.

## Code Style

- Python: follow PEP 8 where practical
- Shell scripts: keep them POSIX-compatible where possible
- Markdown: use `#` for top-level headings, `##` for sections
