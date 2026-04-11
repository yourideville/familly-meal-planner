# Testing and Coverage Gate

- Every behavior change requires automated tests in the same PR/commit scope.
- **Every bug fix must include a non-regression test** that reproduces the original failure scenario and verifies the fix. This applies to both backend (pytest) and frontend (Playwright) tests.
- Minimum required unit test coverage is 80%; treat anything lower as a failed review.
- Prefer fast, deterministic tests with isolated setup/teardown and no shared mutable leftovers.
- Cover success path, validation path, and at least one error path for each touched endpoint/service.
- When coverage cannot be measured, treat it as failing and fix test tooling first.
- Report test command, pass/fail status, and measured coverage in the final review output.
