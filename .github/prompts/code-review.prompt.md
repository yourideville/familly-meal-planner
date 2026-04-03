---
description: "Comprehensive parallel code review delegated to frontend, backend, and aws-devops specialist agents"
tools: [agent, execute, read, search, edit, todo]
---

Perform a comprehensive code review by delegating to three specialist agents **in parallel**.

## Parameters
- **scope** (string, optional): Review scope. Accepted values: `staged`, `branch`, `all`. Default: `branch`.
- **base_branch** (string, optional): Base branch for diff comparisons when scope is `branch`. Default: `main`.
- **min_coverage** (number, optional): Minimum required unit test coverage percentage. Default: `80`.
- **strict_mode** (boolean, optional): If `true`, fail review when critical issues or low coverage are found. Default: `true`.

## Orchestration Steps

### 1. Prepare context
- Run `git status` and `git diff --stat` to identify changed files.
- Based on `scope`:
  - `staged`: collect staged files via `git diff --cached --name-only`
  - `branch`: collect changed files via `git diff --name-only {{base_branch}}...HEAD`
  - `all`: consider the full repository
- Determine today's date in `yyyy-MM-dd` format for the output folder.
- Create the output directory: `docs/code-review/<yyyy-MM-dd>/`

### 2. Delegate to specialist agents in parallel
Run all three subagents **simultaneously** using `runSubagent`. Each agent receives the list of changed files relevant to its domain, the review parameters, and must write its review to a markdown file.

#### Frontend agent (`frontend`)
Prompt the `frontend` agent with:
> Review all changed frontend files (`frontend/**`). Follow the review approach defined in your agent instructions.
> Parameters: scope={{scope}}, min_coverage={{min_coverage}}, strict_mode={{strict_mode}}.
> Changed files in scope: <list only frontend/** files>
> If no frontend files changed, write a short "No frontend changes to review" note.
>
> Review criteria: coding style, component architecture, TypeScript strictness, accessibility, French UI text extraction, performance, and Playwright test coverage.
>
> Write the full review to `docs/code-review/<yyyy-MM-dd>/frontend-review.md` using the Output Format below.
> Return a brief summary of your findings.

#### Backend agent (`backend`)
Prompt the `backend` agent with:
> Review all changed backend files (`backend/**`). Follow the review approach defined in your agent instructions.
> Parameters: scope={{scope}}, min_coverage={{min_coverage}}, strict_mode={{strict_mode}}.
> Changed files in scope: <list only backend/** files>
> If no backend files changed, write a short "No backend changes to review" note.
>
> Review criteria: coding style, FastAPI architecture (thin routers, service layer), Pydantic schemas, type hints, error handling, and pytest coverage.
> Run `pytest --cov=app --cov-report=term-missing` in `backend/` and report results.
>
> Write the full review to `docs/code-review/<yyyy-MM-dd>/backend-review.md` using the Output Format below.
> Return a brief summary of your findings.

#### AWS DevOps agent (`aws-devops`)
Prompt the `aws-devops` agent with:
> Review all changed infrastructure files (`infra/**`, `docker-compose.yml`, `**/Dockerfile`, CI/CD configs). Follow the review approach defined in your agent instructions.
> Parameters: scope={{scope}}, strict_mode={{strict_mode}}.
> Changed files in scope: <list only infra/**, docker-compose.yml, Dockerfile files>
> If no infrastructure files changed, write a short "No infrastructure changes to review" note.
>
> Review criteria: IAM least-privilege, secrets management, stack separation, CDK test coverage, cost optimization, and Well-Architected alignment.
> Run `cdk synth` if CDK files changed. Run CDK tests with `pytest` in `infra/cdk/` if test files exist.
>
> Write the full review to `docs/code-review/<yyyy-MM-dd>/aws-review.md` using the Output Format below.
> Return a brief summary of your findings.

### 3. Consolidate and summarize
After all three agents complete:
1. Read the three review files from `docs/code-review/<yyyy-MM-dd>/`.
2. Present a unified summary to the user with:
   - Per-domain status (frontend / backend / aws-devops)
   - Combined critical findings
   - Global score (average of the three domain scores)
   - Overall review status

## Review File Output Format (for each agent)

Each agent must write its review markdown file with this structure:

```markdown
# <Domain> Code Review — <yyyy-MM-dd>

## Review Scope
- Scope: <staged|branch|all>
- Files reviewed: <count>
- Changed files: <list>

## Findings

### Critical
<must-fix defects, security issues, architecture breaks, coverage below threshold>

### Major
<high-impact maintainability/performance/readability issues>

### Minor
<low-impact style or cleanup suggestions>

## Coverage Summary
- Test command: <command used>
- Result: <pass/fail>
- Coverage: <X%> (target: >= <min_coverage>%)
- Untested critical paths: <list>

## Score Breakdown
| Category               | Score (/10) |
|------------------------|-------------|
| Coding style           | X           |
| Architecture           | X           |
| Performance & readability | X        |
| Tests & coverage       | X           |

## Global Note: X/10

## Review Status
<APPROVED | APPROVED WITH SUGGESTIONS | CHANGES REQUIRED>

## Recommended Next Actions
<actionable list>
```

## Decision Logic
- If `strict_mode=true` and any domain has a Critical finding or coverage below threshold → **CHANGES REQUIRED**
- Otherwise → **APPROVED WITH SUGGESTIONS** or **APPROVED**

## Examples
- `/code-review scope=branch base_branch=main`
- `/code-review scope=staged min_coverage=85`
- `/code-review scope=all min_coverage=80 strict_mode=true`
