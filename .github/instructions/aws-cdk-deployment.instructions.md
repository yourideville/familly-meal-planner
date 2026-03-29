---
description: AWS CDK deployment guidance for the Family Meal Planner application
applyTo: infra/cdk/**/*.py
---

# AWS CDK Deployment Instructions

- Use the Python CDK app in `infra/cdk` for infrastructure deployment.
- Activate the local Python virtual environment before any Python command.
  - Use: `source /home/youri/Projects/Sources/.venv/bin/activate`
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
  - Local behavior should use in-memory persistence.
  - AWS persistence in Lambda should be enabled only by explicit environment configuration.
- Keep deployment stacks separated when reasonable: data, backend, frontend.
- Add CDK unit tests in `infra/cdk/tests/` using `aws_cdk.assertions.Template`.
- Document deployment output URLs and required environment variables in the repo README.
