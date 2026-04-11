# Family Meal Planner MVP

Very simple local MVP:
- Backend: FastAPI with in-memory data (no persistence).
- Frontend: React + Vite.

## Prerequisites

- Python 3.12
- Node.js 20+
- Docker and Docker Compose (optional for local run)
- AWS CLI configured with credentials for deployment
- Repository virtual environment: `source /home/youri/Projects/Sources/.venv/bin/activate`

## Run locally with Docker Compose

From the repo root:

```bash
docker compose up -d --build
```

Then open:
- Frontend: http://localhost:5173
- Backend API docs: http://localhost:8000/docs

Stop the application:

```bash
docker compose down
```

## Run locally without Docker

Activate the repo virtual environment first:

```bash
source /home/youri/Projects/Sources/.venv/bin/activate
```

Start the backend:

```bash
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Start the frontend in another terminal:

```bash
cd frontend
npm install
npm run dev
```

Then open:
- Frontend: http://localhost:5173
- Backend API docs: http://localhost:8000/docs

## Build the frontend

Before deploying to AWS, build the frontend assets:

```bash
cd frontend
npm install
npm run build
```

This creates the production files in `frontend/dist`.

## Deploy to AWS

The AWS deployment is managed by the CDK app in `infra/cdk`.

From the repo root:

```bash
source /home/youri/Projects/Sources/.venv/bin/activate
cd infra/cdk
python -m pip install -r requirements.txt
```

Build the frontend before deployment:

```bash
cd ../../frontend
npm install
npm run build
cd ../infra/cdk
```

Deploy with CDK:

```bash
npx --yes cdk bootstrap
npx --yes cdk synth --no-color
npx --yes cdk deploy --all --require-approval never
```

If your shell supports it, you may also use `activate-python`, but prefer the explicit `source /home/youri/Projects/Sources/.venv/bin/activate` command.

### CDK stacks

The CDK app deploys separate stacks for infrastructure:
- `DynamoDbStack` for DynamoDB persistence tables
- `BackendStack` for the Lambda API and HTTP API
- `FrontendStack` for the S3 bucket and CloudFront distribution

## Admin password configuration

The backend now stores the admin password in AWS Systems Manager Parameter Store as a string parameter. The parameter is created at deploy time at:

- `/family-meal-planner/<stage>/admin-password`

It is seeded with a placeholder value `CHANGEME` and should be updated manually before using admin login.

## Data upload and cleanup script

A management script is available at `scripts/manage_data.py`.

Example usage:

```bash
source /home/youri/Projects/Sources/.venv/bin/activate
python scripts/manage_data.py \
  --api-url http://localhost:8000 \
  --admin-password YOUR_ADMIN_PASSWORD \
  --members-csv scripts/sample_members.csv \
  --dishes-csv scripts/sample_dishes.csv
```

To delete all dishes and members from the backend:

```bash
python scripts/manage_data.py --api-url http://localhost:8000 --admin-password YOUR_ADMIN_PASSWORD --cleanup
```

## Notes

- Frontend assets must be built before deployment so CDK can publish `frontend/dist` into the S3 bucket.
- The CloudFront stack is configured to limit price class to North America and Europe.

## Testing

The project includes comprehensive automated tests for both backend and frontend.

### Backend tests

```bash
cd backend
source /home/youri/Projects/Sources/.venv/bin/activate

# Run all tests with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_auth.py -v

# Generate HTML coverage report
pytest --cov=app --cov-report=html
# Then open: htmlcov/index.html
```

**Test coverage:** 145 tests, 72% coverage (91 new tests added)

### Frontend tests

#### Unit Tests (Vitest)

```bash
cd frontend
npm install

# Run unit tests
npm run test:unit

# Run with coverage
npm run test:unit:coverage

# Run in watch mode (for development)
npm run test:unit:watch
```

**Test coverage:** 15 unit tests covering constants and components

#### E2E Tests (Playwright)

```bash
cd frontend
npx playwright install

# Run E2E tests
npm run test

# Run Playwright UI tester
npm run test:ui
```

### Test Documentation

- **Detailed coverage analysis:** `docs/test-coverage-analysis.md`
- **Testing summary:** `docs/testing-summary.md`
- **HTML coverage report:** `backend/htmlcov/index.html` (after running tests)
