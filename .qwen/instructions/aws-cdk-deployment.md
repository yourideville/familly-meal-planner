# AWS CDK Deployment Instructions

- Use the Python CDK app in `infra/cdk` for infrastructure deployment.
- Activate the local Python virtual environment before any Python command.
  - Use: `source /home/ydeville/Projects/Sources/python3.13/bin/activate`
  - If `activate-python` is available, it may also work, but prefer the explicit `source` command.
- Install CDK dependencies in `infra/cdk` with:
  ```bash
  python -m pip install -r requirements.txt
  ```
- Run the CDK CLI via `npx --yes cdk` to avoid requiring a global install.
- Use these deployment commands in sequence:
  1. `npx --yes cdk bootstrap`
  2. `npx --yes cdk synth`
  3. `npx --yes cdk deploy`
- Keep the backend code testable and offline by default.
  - Local behavior should use in-memory persistence (`BACKEND_PERSISTENCE_MODE=inmemory`).
  - AWS persistence in Lambda should be enabled by setting `BACKEND_PERSISTENCE_MODE=dynamodb`.
- Keep deployment stacks separated when reasonable: data, backend, frontend.
- Add CDK unit tests in `infra/cdk/tests/` using `aws_cdk.assertions.Template`.
- Document deployment output URLs and required environment variables in the repo README.

## Free Tier Guidelines
- All resources must stay within the AWS Free Tier.
- DynamoDB: use `PAY_PER_REQUEST` billing mode (free tier: 25 WCU + 25 RCU).
- Lambda: single function, reasonable timeout (30s max). Free tier: 1M requests/month.
- API Gateway: use HTTP API (cheaper than REST API). Free tier: 1M requests/month.
- CloudFront: `PRICE_CLASS_100` (cheapest). Free tier: 1TB + 10M requests/month.
- Do NOT use SSM SecureString (CloudFormation cannot create it). Pass `ADMIN_PASSWORD` as a plain Lambda env var.
- Use `RemovalPolicy.DESTROY` for dev stage to avoid orphaned resources and charges.
