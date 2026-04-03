# Family Meal Planner Guidelines

## Language Requirements
- **Code**: All variable names, function names, classes, imports, and code logic must be in **English**.
- **Documentation & Comments**: All docstrings, comments, commit messages, and planning documents (plan.md) must be in **English**.
- **UI Only**: User-facing text (labels, buttons, error messages, page titles) can be in **French** since this is for a French family.

## Code Style
- **Backend**: Follow FastAPI architecture rules in [.github/instructions/backend-fastapi-architecture.instructions.md](.github/instructions/backend-fastapi-architecture.instructions.md)
- **Frontend**: Follow React TypeScript rules in [.github/instructions/frontend-react-typescript.instructions.md](.github/instructions/frontend-react-typescript.instructions.md)

## Architecture
- **Backend**: FastAPI with layered architecture (routers → services → schemas).
  - **Local development**: Uses in-memory data store by default (`BACKEND_PERSISTENCE_MODE=inmemory`).
  - **AWS deployment**: Uses DynamoDB for persistence (`BACKEND_PERSISTENCE_MODE=dynamodb`).
- **Frontend**: React with TypeScript, page-based routing (Catalog, Voting, WeeklyMenu). API client for backend communication.
- **Overall**: Docker Compose for local development, CORS configured for frontend.

## Storage Strategy
- The store module (`app/services/store.py`) supports two backends selected by `BACKEND_PERSISTENCE_MODE` env var:
  - `inmemory` (default): All data held in module-level dictionaries. Suitable for local dev and tests.
  - `dynamodb`: Reads/writes to DynamoDB tables. Requires `DISHES_TABLE_NAME`, `MEMBERS_TABLE_NAME`, `VOTES_TABLE_NAME` env vars.
- boto3 is only imported when `BACKEND_PERSISTENCE_MODE=dynamodb`.
- Tests always run against the in-memory backend.

## Admin Authentication
- Admin login uses a single shared password (no per-user accounts).
- Password source priority: `ADMIN_PASSWORD_PARAMETER_NAME` env var (SSM lookup) → `ADMIN_PASSWORD` env var → fallback `"password"`.
- For local dev, the default password `"password"` is used.
- For AWS, the admin password is stored as a **manually created SSM SecureString** parameter.
  - Parameter name convention: `/family-meal-planner/<stage>/admin-password`
  - Create it once before first deploy: `aws ssm put-parameter --name /family-meal-planner/dev/admin-password --value "<your-password>" --type SecureString`
  - CDK passes only the parameter **name** to Lambda; it does NOT create the parameter itself.
  - The Lambda reads it with `WithDecryption=True` at runtime.
  - If the parameter does not exist yet, the app falls back to the `ADMIN_PASSWORD` env var.

## AWS Free Tier Constraints
- All AWS resources must stay within the AWS Free Tier.
- DynamoDB: use on-demand (PAY_PER_REQUEST) billing — free for up to 25 WCU/25 RCU.
- Lambda: free for up to 1M requests/month.
- API Gateway HTTP API: free for up to 1M requests/month (first 12 months).
- CloudFront: 1TB data transfer + 10M requests/month free (first 12 months).
- SSM SecureString cannot be created by CloudFormation/CDK — create it manually via CLI or console.
- Avoid SSM SecureString (not supported by CloudFormation). Use plain env vars or SSM String parameters.

## Build and Test
- **Full stack**: `docker compose up --build` (frontend: http://localhost:5173, backend: http://localhost:8000/docs)
- **Python commands**: activate the repository Python environment before running any Python command or test.
  - Use: `source /home/ydeville/Projects/Sources/python3.13/bin/activate`
  - If `activate-python` is available, it may also work, but prefer the explicit `source` command.
- **Backend tests**: `pytest` in backend/ directory, minimum 80% coverage enforced. See [.github/instructions/testing-coverage-gate.instructions.md](.github/instructions/testing-coverage-gate.instructions.md)
- **Frontend**: `npm run dev` for development, `npm run build` for production.
- **AWS deployment**: use the CDK app in `infra/cdk` and follow `.github/instructions/aws-cdk-deployment.instructions.md`.

## Conventions
- Use French text **only** for UI labels, buttons, and user-facing error messages (display strings).
- Code identifiers (variable, function, class names) must always be in English.
- Keep services deterministic for testability (resettable state).
- Explicit Pydantic response models in all API endpoints.
- Type hints on all backend functions.
- Store shared constants in dedicated files (e.g., `constants/weekdays.ts`).
- Never import `boto3` at module level in code that runs locally; gate imports behind `BACKEND_PERSISTENCE_MODE` checks.