# AWS Serverless Deployment Plan

## Goals

Build a first AWS production-like deployment using CDK Python, with:

- backend FastAPI packaged as AWS Lambda on `python3.11` ARM
- persistence in DynamoDB in serverless mode
- API Gateway HTTP API for the backend
- static frontend hosting via S3 and CloudFront
- CDK unit tests and backend pytest coverage
- local quick testing with in-memory persistence by default

## Steps

1. Set up the `infra/cdk` app structure.
   - Add `infra/cdk/app.py` as the CDK entrypoint.
   - Create `infra/cdk/stacks/dynamodb_stack.py` for DynamoDB tables.
   - Create `infra/cdk/stacks/backend_stack.py` for Lambda, API Gateway, and IAM permissions.
   - Create `infra/cdk/stacks/frontend_stack.py` for S3 static site hosting and optional CloudFront.
   - Add `infra/cdk/requirements.txt` for CDK dependencies and Python unit test dependencies.

2. Define the serverless data layer in CDK.
   - Use DynamoDB on-demand billing and keys that fit the current app domain.
   - Create tables for `Dishes`, `Members`, `Votes`, and `WeeklyMenus` in `dynamodb_stack.py`.
   - Export table ARNs / names from `DynamoDbStack` so `BackendStack` can reference them.
   - Keep item design minimal and free-tier friendly.

3. Wire the backend Lambda + API Gateway.
   - Use `aws_lambda_python_alpha.PythonFunction` or CDK bundling to package the backend code from `backend/`.
   - Select runtime `python3.11` and architecture `ARM_64` for lower cost.
   - Use HTTP API Gateway to proxy all paths to the Lambda.
   - Add environment variables for table names, stage, and optional CORS settings.
   - Grant the Lambda read/write permissions to the DynamoDB tables.

4. Add frontend static hosting.
   - Create a private S3 bucket for the built frontend assets.
   - Add a CloudFront distribution with the S3 bucket as origin for HTTPS access.
   - Configure the frontend build to use `VITE_API_BASE_URL` from the deployed API Gateway URL.
   - Optionally keep a simple S3 static website setup if CloudFront is too complex for MVP.

5. Refactor the backend for persistence.
   - Keep the existing in-memory `backend/app/services/store.py` for local quick testing.
   - Add a persistence adapter layer that selects between `memory` and `dynamodb` based on an environment variable such as `BACKEND_PERSISTENCE_MODE`.
   - Implement DynamoDB-backed data access in `backend/app/db/dynamodb_store.py` or similar.
   - Use `boto3` in the backend to read/write DynamoDB tables from Lambda and, optionally, from local DynamoDB if `DYNAMODB_ENDPOINT_URL` is configured.
   - Keep the existing router signatures and response models; swap the implementation behind the service layer.
   - Add a `backend/app/core/aws.py` or config helper to read environment variables and instantiate DynamoDB clients.
   - Add `mangum` adapter entrypoint if needed for Lambda compatibility.

6. Update backend dependencies.
   - Add `boto3` and `mangum` to `backend/requirements.txt`.
   - If any new dependency is required for Lambda packaging, add it under `infra/cdk/requirements.txt`.
   - Document local use: default to in-memory mode with no AWS config required, and provide optional local DynamoDB support.

7. Add unit tests for infrastructure and backend behavior.
   - Add CDK stack tests under `infra/cdk/tests/` using `aws_cdk.assertions.Template`.
   - Verify that `DynamoDbStack` creates the expected tables and key schema.
   - Verify that `BackendStack` creates one Lambda function, HTTP API, and correct IAM policy statements for DynamoDB access.
   - Add backend pytest tests for the new persistence adapter and environment-backed config.
   - Verify the default local persistence mode remains in-memory and that `BACKEND_PERSISTENCE_MODE=dynamodb` switches to DynamoDB behavior.
   - Preserve the existing `backend/tests/conftest.py` fixture style; extend it for AWS client mocking if needed.

8. Document deployment and local build steps.
   - Add or update `README.md` with `cdk bootstrap` and `cdk deploy` commands.
   - Document how to build the frontend and deploy it with CDK, including `VITE_API_BASE_URL` injection.
   - Note that the AWS account is already configured and the region selection should be explicit in commands.

## Relevant files

- `infra/cdk/app.py` — CDK entrypoint and stack instantiation.
- `infra/cdk/stacks/dynamodb_stack.py` — serverless persistence resources.
- `infra/cdk/stacks/backend_stack.py` — Lambda + API Gateway + permissions.
- `infra/cdk/stacks/frontend_stack.py` — static website hosting.
- `infra/cdk/requirements.txt` — CDK and test dependencies.
- `backend/app/main.py` — Lambda-friendly FastAPI app registration.
- `backend/app/db/` or `backend/app/services/` — DynamoDB persistence layer.
- `backend/requirements.txt` — add `boto3` and `mangum`.
- `backend/tests/` — extend existing tests to cover DynamoDB-backed behavior.

## Verification

1. Run backend tests with `pytest --cov=app --cov-report=term-missing` and ensure coverage stays above 80%.
2. Run CDK unit tests in `infra/cdk/tests/` and verify the template contains resources for Lambda, API Gateway, and DynamoDB.
3. Run `cdk synth` and `cdk diff` in `infra/cdk/` to confirm the deployment plan.
4. Deploy to AWS using `cdk deploy` in a prepared region and verify the HTTP API endpoint returns health data and the frontend is publicly accessible.
5. Confirm the deployed frontend uses the API Gateway URL from the CDK output.

## Decisions

- Use Python CDK and AWS Lambda ARM_64 for cost efficiency.
- Use API Gateway HTTP API rather than ALB, matching the cheaper serverless requirement.
- Include frontend hosting in the first deployment so the site is accessible from everywhere.
- Keep DynamoDB in on-demand mode for serverless free-tier-friendly use.
- Preserve the current in-memory persistence locally and use DynamoDB only in deployed or explicitly configured modes.

## Further considerations

1. If you want absolute minimum complexity, the first version can host the frontend on S3 only and add CloudFront later.
2. We should decide whether to use a single combined CDK stack or separate stacks for backend, data, and frontend; I recommend separate stacks for clearer test boundaries.
3. We will need to add `boto3` mocks or local DynamoDB test support if backend tests should stay deterministic and offline.
