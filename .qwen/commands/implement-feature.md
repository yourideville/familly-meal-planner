---
name: implement-feature
description: "Read a provided feature plan and implement the requested functionality according to the repository architecture."
---

Read a provided feature plan and implement the requested functionality according to the repository architecture, backend/frontend conventions, and testing requirements. The implementation should respect FastAPI service/schema layering, React TypeScript page/component structure, French UI text rules, and the 80% coverage gate.

## Parameters
- **plan** (string, required): The feature plan, requirements, or design notes to implement.
- **scope** (string, optional): One of `backend`, `frontend`, `fullstack`, or `docs`. Defaults to `fullstack` when unspecified.
- **focus** (string, optional): Additional guidance such as `API contract`, `UI flow`, `business logic`, or `tests`.

## Command
1. Read the full `plan` carefully and extract:
   - what user problem the feature solves
   - required backend endpoints, data models, or services
   - required frontend pages, components, or user interactions
   - expected validation, error handling, and user-facing messages
2. Review repository guidelines before changing code:
   - `.qwen/instructions/project-guidelines.md`
   - `.qwen/instructions/backend-fastapi-architecture.md`
   - `.qwen/instructions/frontend-react-typescript.md`
   - `.qwen/instructions/testing-coverage-gate.md`
3. Determine the correct implementation layer:
   - backend: routers validate requests and delegate to services; services contain domain logic; schemas define explicit Pydantic models
   - frontend: pages orchestrate data/fetching; components/hooks hold reusable UI logic; shared constants and typed domain contracts live in `constants/` and `types/`
4. Implement the feature using English identifiers for code and French only for user-facing UI labels, buttons, and error messages.
5. Keep backend services deterministic and in-memory for MVP behavior.
6. Add or update automated tests for every behavior change:
   - backend tests in `backend/tests/`
   - frontend tests if applicable using existing project tooling
   - cover success path, validation path, and at least one error path for touched functionality
7. Verify new work does not decrease coverage below 80%.
8. When applicable, update docs or README with the new feature summary.
9. Summarize the final implementation in a concise report:
   - files changed
   - new or updated API routes
   - frontend pages/components affected
   - tests added or updated
   - any relevant design or constraint notes

## Output format
- Summary of implementation scope
- Key changed files
- API contract and UI behavior
- Tests added/updated
- Coverage verification note

## Example invocation
`/implement-feature plan="Add voting categories and admin page support" scope=fullstack`
