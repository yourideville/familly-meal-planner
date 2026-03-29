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
cd ../frontend
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

## Notes

- Frontend assets must be built before deployment so CDK can publish `frontend/dist` into the S3 bucket.
- The CloudFront stack is configured to limit price class to North America and Europe.

## Testing

### Backend tests

```bash
cd backend
source /home/youri/Projects/Sources/.venv/bin/activate
pytest --cov=app --cov-report=term-missing
```

### Frontend tests

```bash
cd frontend
npm install
npx playwright install
npm run test
```

Or run the Playwright UI tester:

```bash
npm run test:ui
```
