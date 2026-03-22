# Family Meal Planner Guidelines

## Language Requirements
- **Code**: All variable names, function names, classes, imports, and code logic must be in **English**.
- **Documentation & Comments**: All docstrings, comments, commit messages, and planning documents (plan.md) must be in **English**.
- **UI Only**: User-facing text (labels, buttons, error messages, page titles) can be in **French** since this is for a French family.

## Code Style
- **Backend**: Follow FastAPI architecture rules in [.github/instructions/backend-fastapi-architecture.instructions.md](.github/instructions/backend-fastapi-architecture.instructions.md)
- **Frontend**: Follow React TypeScript rules in [.github/instructions/frontend-react-typescript.instructions.md](.github/instructions/frontend-react-typescript.instructions.md)

## Architecture
- **Backend**: FastAPI with layered architecture (routers → services → schemas). In-memory data store for MVP, planned DynamoDB persistence.
- **Frontend**: React with TypeScript, page-based routing (Catalog, Voting, WeeklyMenu). API client for backend communication.
- **Overall**: Docker Compose for local development, CORS configured for frontend.

## Build and Test
- **Full stack**: `docker compose up --build` (frontend: http://localhost:5173, backend: http://localhost:8000/docs)
- **Backend tests**: `pytest` in backend/ directory, minimum 80% coverage enforced. See [.github/instructions/testing-coverage-gate.instructions.md](.github/instructions/testing-coverage-gate.instructions.md)
- **Frontend**: `npm run dev` for development, `npm run build` for production.

## Conventions
- Use French text **only** for UI labels, buttons, and user-facing error messages (display strings).
- Code identifiers (variable, function, class names) must always be in English.
- Keep services deterministic for testability (resettable state).
- Explicit Pydantic response models in all API endpoints.
- Type hints on all backend functions.
- Store shared constants in dedicated files (e.g., `constants/weekdays.ts`).