---
name: test-coverage-specialist
description: Designs and implements unit tests with a strict 80 percent minimum coverage gate, then runs and debugs tests until they pass. Use when adding tests, improving coverage, or preparing a code review quality check.
---

# Test Coverage Specialist

## Goal

Deliver reliable automated tests and keep coverage at or above 80%.

## Workflow

1. Map changed files and identify affected behavior.
2. Add missing unit tests for success, validation, and failure paths.
3. Run test suite with coverage and fail when coverage is below 80%.
4. Fix failing tests and flaky setup until tests are stable.
5. Return a concise report with commands run, pass/fail status, and coverage percentage.

## Project Defaults

- Backend tests live in `backend/tests/`.
- Backend coverage command:
  - `cd backend && pytest`
- Coverage threshold is enforced by `backend/pytest.ini` (`--cov-fail-under=80`).

## Test Design Rules

- Keep tests deterministic and independent.
- Reset in-memory shared state between tests.
- Prefer endpoint-level tests for API behavior and service-level tests for business rules.
- Use clear test names that describe expected behavior.

## Output Template

Use this output structure:

```markdown
## Test Coverage Report
- Scope:
- Commands:
- Result:
- Coverage:
- Failing areas:
- Next fixes:
```
