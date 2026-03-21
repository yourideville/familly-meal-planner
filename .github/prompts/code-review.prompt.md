## Name
Comprehensive code review

## Description
Perform a complete code review focused on coding style, software architecture, performance/readability, and test coverage. Return clear findings, actionable fixes, and a final score (note).

## Parameters
- **scope** (string, optional): Review scope. Accepted values: `staged`, `branch`, `all`. Default: `branch`.
- **base_branch** (string, optional): Base branch for diff comparisons when scope is `branch`. Default: `main`.
- **min_coverage** (number, optional): Minimum required unit test coverage percentage. Default: `80`.
- **strict_mode** (boolean, optional): If `true`, fail review when critical issues or low coverage are found. Default: `true`.

## Command
1. Establish review scope:
   - If `scope=staged`: review only staged files.
   - If `scope=branch`: review changes from `base_branch...HEAD`.
   - If `scope=all`: review the whole repository.
2. Collect context:
   - Run `git status`, `git diff --stat`, and the relevant `git diff`.
   - Identify changed modules, entry points, shared utilities, and tests.
3. Coding style review:
   - Check consistency: naming, formatting, file/module organization, comments quality.
   - Verify standards usage: lint/formatter conventions and project idioms.
   - Flag duplicated logic, magic numbers/strings, unclear abstractions, and weak error handling.
4. Software architecture review:
   - Evaluate separation of concerns, coupling/cohesion, dependency direction, and boundaries.
   - Validate API contracts, state management choices, and domain layering.
   - Report architectural risks (tight coupling, hidden side effects, leaky abstractions).
5. Performance and readability review:
   - Identify unnecessary re-renders, expensive loops, redundant data transforms, and avoidable allocations.
   - Detect N+1/network inefficiencies, blocking calls, and missing caching/memoization where relevant.
   - Assess readability: function size, intent clarity, variable naming, and complexity hotspots.
6. Unit test and coverage review:
   - Run unit tests for touched areas (or all tests if needed).
   - Compute coverage using project tooling (`pytest --cov`, `vitest --coverage`, `jest --coverage`, etc.).
   - Compare measured coverage against `min_coverage` (default `80`).
   - Highlight untested critical paths and propose specific missing test cases.
7. Report findings ordered by severity:
   - **Critical**: must-fix defects, security issues, architecture breaks, or coverage below threshold.
   - **Major**: high-impact maintainability/performance/readability issues.
   - **Minor**: low-impact style or cleanup suggestions.
8. Give a final note (score out of 10) with weighted rubric:
   - Coding style: 25%
   - Architecture: 25%
   - Performance & readability: 25%
   - Tests & coverage: 25%
   - Include both:
     - `Global note: X/10`
     - `Coverage: Y% (target: >= min_coverage%)`
9. Decision output:
   - If `strict_mode=true` and any Critical issue exists (including coverage below threshold), mark **Review status: CHANGES REQUIRED**.
   - Otherwise mark **Review status: APPROVED WITH SUGGESTIONS** (or **APPROVED** when no significant issues).

## Output format
- **Review scope**
- **Findings**
  - Critical
  - Major
  - Minor
- **Coverage summary**
- **Score breakdown**
- **Global note**
- **Review status**
- **Recommended next actions**

## Examples
- Review branch against main with default threshold:
  - `/code-review scope=branch base_branch=main`
- Review staged files with stricter coverage target:
  - `/code-review scope=staged min_coverage=85`
- Full repository health check:
  - `/code-review scope=all min_coverage=80 strict_mode=true`
