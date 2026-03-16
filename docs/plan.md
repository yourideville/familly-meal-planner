## Architecture & Implementation Plan

### High-level goals

- **Web app** for family weekly dish menu.
- **Catalog of dishes** stored in DynamoDB.
- **Voting flow** so all family members can vote for next week’s dishes.
- **Notifications/reminders** (later).
- **External recipe API integration** (e.g. Spoonacular) for suggestions.
- **Menu generation** for the week based on votes/preferences.

Stack choices:

- **Frontend**: React + TypeScript (Vite).
- **Backend**: Python (FastAPI-style app, packaged for Lambda).
- **Infra & deployment**: **AWS CDK (Python)**.
- **Database**: DynamoDB.

---

### Repository structure

- `backend/`
  - `app/`
    - `routers/` – HTTP routes (dishes, users, votes, weekly-menu, health, etc.).
    - `models/` – domain models/entities (Dish, User, Vote, WeeklyMenu).
    - `schemas/` – Pydantic schemas for requests/responses.
    - `services/` – business logic (voting, weekly menu generation, integrations).
    - `core/` – settings, configuration, security utilities.
    - `db/` – DynamoDB access layer, table abstractions.
  - `tests/` – backend unit/integration tests.

- `frontend/`
  - `src/`
    - `components/` – reusable UI components.
    - `pages/` – route-level pages (catalog, voting, weekly menu, settings).
    - `hooks/` – custom React hooks (API calls, auth, state).
    - `api/` – API client layer (typed wrappers over HTTP calls).
    - `types/` – shared TypeScript types/interfaces.
    - `styles/` – global styles, theme configuration.

- `infra/`
  - `cdk/`
    - (to be added) `app.py` – CDK entry point.
    - (to be added) `stacks/` – CDK stacks:
      - `backend_stack.py` – API Gateway + Lambda (Python) + permissions.
      - `dynamodb_stack.py` – DynamoDB tables and indexes.
      - (optional later) `frontend_stack.py` – S3 + CloudFront for SPA hosting.

- `docs/`
  - `plan.md` – this document and future refinements.

---

### Backend (Python + Lambda)

- **Framework**: FastAPI (or Starlette) for ergonomic route definitions and validation.
- **Runtime**: Python 3.11 on AWS Lambda.
- **Integration**: `mangum` to adapt ASGI app to Lambda/APIGW.

Key responsibilities:

- Manage **dishes catalog** (CRUD).
- Handle **user registration/auth** (simple JWT-based MVP).
- Accept and store **votes** for upcoming week.
- Expose **menu generation** endpoint that builds a weekly menu from votes and preferences.
- Provide **read APIs** for frontend: catalog, current week menu, historical menus.

Data storage:

- **DynamoDB**:
  - `Dishes` table – dish metadata, tags, difficulty, external API references.
  - `Users` table – family members, preferences, roles.
  - `Votes` table – votes for dishes/time slots.
  - `Menus` table – generated weekly menus.

---

### Frontend (React + TypeScript)

- **App type**: Single Page Application.
- **Tooling**: Vite (React + TS template).
- **Routing**: `react-router-dom`.
- **Data fetching**: `@tanstack/react-query` or similar.

Core screens:

- **Dish catalog** – browse, filter, and manage dishes.
- **Voting page** – show candidate dishes and let each family member vote.
- **Weekly menu view** – show generated menu for current/next week.
- **Settings** – manage preferences, notification options (later).

The frontend will call the backend via **API Gateway HTTPS endpoints** created by CDK.

---

### Infrastructure with AWS CDK (Python)

We will use **AWS CDK in Python** instead of SAM templates.

CDK app structure (to be implemented under `infra/cdk/`):

- `app.py`
  - Instantiates one or more stacks (e.g. `BackendStack`, `DynamoDbStack`, optionally `FrontendStack`).

- `stacks/backend_stack.py`
  - Defines:
    - **Lambda function** for the backend:
      - Runtime: `python3.11`.
      - Code from `backend/` (packaged via CDK bundling or `aws_lambda_python_alpha`).
    - **API Gateway**:
      - HTTP or REST API.
      - Routes all requests to the Lambda (proxy integration).
    - IAM permissions for Lambda to access DynamoDB tables.

- `stacks/dynamodb_stack.py`
  - Defines DynamoDB tables:
    - `DishesTable`.
    - `UsersTable`.
    - `VotesTable`.
    - `MenusTable`.
  - Exports table names/ARNs to be used by `BackendStack`.

- (optional later) `stacks/frontend_stack.py`
  - S3 bucket for static frontend hosting.
  - CloudFront distribution.

Deployment workflow (CDK):

1. From `infra/cdk/`:
   - Bootstrap once per account/region:
     - `cdk bootstrap aws://ACCOUNT_ID/REGION`
   - Deploy:
     - `cdk deploy` (or specific stacks, e.g. `cdk deploy BackendStack DynamoDbStack`).

2. CDK synthesizes CloudFormation templates and deploys:
   - DynamoDB tables.
   - Lambda function(s).
   - API Gateway.
   - (later) S3/CloudFront for frontend.

---

### Local development & testing

- **Backend locally**:
  - Run FastAPI app with `uvicorn` (e.g. `uvicorn app.main:app --reload --port 8000`).
  - Point frontend to `http://localhost:8000` during development.

- **Frontend locally**:
  - Run Vite dev server (e.g. `npm run dev`).
  - Use env variable (e.g. `VITE_API_BASE_URL`) to toggle between local backend and deployed API Gateway URL.

- **DynamoDB**:
  - Option A: use **DynamoDB Local** with Docker during dev.
  - Option B: use a dedicated **dev DynamoDB tables** deployed via CDK.

---

### Next steps

1. Initialize **CDK app** in `infra/cdk/` (language: Python).
2. Define **DynamoDB tables** and **backend Lambda + API Gateway** stacks.
3. Scaffold minimal **backend FastAPI app** structure under `backend/app/`.
4. Scaffold **frontend React + TS** project under `frontend/`.
5. Wire environment variables (table names, API base URL) between CDK and backend/frontend.

