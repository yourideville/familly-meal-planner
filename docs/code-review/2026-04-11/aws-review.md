# AWS Infrastructure Review — 2026-04-11

## Review Scope
- **Scope**: branch (`feature/historization-and-optimization`)
- **Files reviewed**: 12
- **Changed files**:
  - `docker-compose.yml`
  - `backend/Dockerfile`
  - `frontend/Dockerfile`
  - `infra/cdk/app.py`
  - `infra/cdk/cdk.json`
  - `infra/cdk/requirements.txt`
  - `infra/cdk/stacks/__init__.py`
  - `infra/cdk/stacks/backend_stack.py`
  - `infra/cdk/stacks/dynamodb_stack.py`
  - `infra/cdk/stacks/frontend_stack.py`
  - `infra/cdk/tests/test_stacks.py`
  - `.github/**` (configuration files — no workflows found)

## Findings

### Critical

1. **No CI/CD Pipeline Defined**
   - There are **zero GitHub Actions workflow files** (`.github/workflows/` is empty).
   - The project has `.github/agents/`, `.github/prompts/`, and `.github/instructions/` but no actual CI pipeline.
   - All testing, building, and deployment is manual. This is a significant risk for a production system — there is no automated gate preventing broken infrastructure or application code from being merged.
   - **Recommendation**: Add at minimum a `ci.yml` workflow that runs backend tests, CDK synth validation, frontend build, and CDK unit tests on every push/PR.

2. **CDK Tests Time Out / Not Reliable**
   - `pytest tests/test_stacks.py` with 3 tests timed out after 120 seconds. CDK synthesis for Lambda + Layer + API Gateway + DynamoDB stacks is slow.
   - The tests are structurally correct but **not viable as a CI gate** without optimization.
   - **Recommendation**:
     - Add `pytest-timeout` with a generous per-test timeout (e.g., 180s) and a total suite timeout.
     - Consider mocking `PythonLayerVersion` bundling in tests to avoid Docker-based `pip install` during synthesis. The bundling step triggers a full Docker build which is the primary cause of timeout.
     - Example fix in test setup:
       ```python
       # Use skip_asset_hash or mock the bundling to skip Docker
       ```

3. **Lambda IAM Policy — SSM Access Not Validated at Deploy Time**
   - `backend_stack.py` grants `ssm:GetParameter` on the admin password parameter, but the **SSM parameter itself is not created by CDK**. It must be created manually before deployment.
   - If the parameter is missing, the Lambda will fail at runtime when trying to read it (depending on application fallback logic).
   - The project guidelines state the app falls back to `ADMIN_PASSWORD` env var, but `ADMIN_PASSWORD` is **not set** in the Lambda environment — only `ADMIN_PASSWORD_PARAMETER_NAME` is passed.
   - **Recommendation**: Either:
     - (a) Add a fallback `ADMIN_PASSWORD` env var in the Lambda definition for bootstrapping, or
     - (b) Create the SSM parameter in CDK as a `StringParameter` (not SecureString, since CloudFormation doesn't support it), or
     - (c) Document this as a manual pre-deployment step in README with clear error consequences.

### Major

4. **CORS `AllowedOrigins: "*"` in Production**
   - `backend_stack.py` sets `CORS_ALLOWED_ORIGINS: "*"` hardcoded. For a production deployment this is overly permissive.
   - **Recommendation**: Parameterize via `CDK_STAGE` — use `"*"` for `dev` but require a specific origin for `prod` (e.g., the CloudFront distribution URL).

5. **Frontend Stack — `RemovalPolicy.DESTROY` + `AutoDeleteObjects` on S3 Bucket**
   - `frontend_stack.py` uses `RemovalPolicy.DESTROY` and `auto_delete_objects=True` for the S3 bucket. This is acceptable for `dev` but risky if accidentally deployed to `prod` stage.
   - **Recommendation**: Conditionally apply `DESTROY` only for `dev` stage, and use `RETAIN` for other stages (same pattern as `dynamodb_stack.py`).

6. **Dockerfile for Backend — Copies Test Files into Production Image**
   - `backend/Dockerfile` copies `tests/` and `pytest.ini` into the image. These are not needed for production runtime and increase image size and attack surface.
   - **Recommendation**: Use a multi-stage build or exclude test files:
     ```dockerfile
     COPY app ./app
     # Remove: COPY tests ./tests
     # Remove: COPY pytest.ini ./pytest.ini
     ```

7. **Dockerfile for Frontend — Development Server in Production**
   - `frontend/Dockerfile` runs `npm run dev` with Vite dev server. This is only appropriate for local development, not for any staging or production use.
   - The docker-compose context is local dev only, but the Dockerfile should be labeled or separated to prevent accidental production use.
   - **Recommendation**: Either rename to `Dockerfile.dev` or add a production multi-stage build that uses `nginx` or `node:alpine` with a static file server for the built `dist/` output.

8. **No CloudFront OAC (Origin Access Control) for S3 — Uses Legacy OAI Pattern**
   - `frontend_stack.py` uses `S3BucketOrigin.with_origin_access_control()` which is correct (OAC is the modern approach, replacing OAI). However, the S3 bucket policy is not explicitly verified. CDK should auto-generate it, but this is worth confirming during deployment.
   - **Recommendation**: Verify during first deployment that the bucket policy grants CloudFront OAC access. Add a comment in code confirming this behavior.

9. **API Gateway HTTP API Has No Custom Domain**
   - The backend API uses the default `*.execute-api.*.amazonaws.com` URL. The CloudFront distribution proxies to it via `/api/*` path, which is acceptable. However, the raw API URL is exposed in the `BackendApiUrl` output.
   - **Recommendation**: For production, consider adding a custom domain with ACM certificate. For the current MVP scope, this is acceptable but should be documented.

10. **Frontend Stack — Inline CloudFront Function for `/api` Prefix Stripping**
    - The `_STRIP_API_PREFIX_JS` function strips `/api` prefix before forwarding to API Gateway. This is functional but fragile — if the API Gateway path changes, the function must be updated manually.
    - **Recommendation**: Extract this to a separate file (e.g., `infra/cdk/assets/strip-api-prefix.js`) so it can be versioned independently and tested.

### Minor

11. **Lambda Timeout of 30s Is Generous for This Workload**
    - The backend Lambda has a 30-second timeout. For a family meal planner with in-memory/DynamoDB operations, this is excessive. Most requests should complete in <1s.
    - **Recommendation**: Reduce to 10s for cost optimization and faster failure detection. Keep DynamoDB cold-start tolerance in mind (still should be <5s).

12. **No Stage-Specific Naming for Lambda Layers**
    - The Lambda layer (`BackendDepsLayer`) does not include the `stage` in its logical ID, which means deploying `dev` and `prod` in the same account/region would create naming conflicts at the CloudFormation level (though stacks would be separate).
    - **Recommendation**: Include `stage` in the layer construct ID: `f"BackendDepsLayer-{stage}"`.

13. **`cdk.json` Minimal — No Context or Feature Flags**
    - `cdk.json` only contains `{"app": "python3 app.py"}`. No CDK feature flags or context values are set.
    - **Recommendation**: Add recommended CDK feature flags for newer constructs to avoid deprecation warnings:
      ```json
      {
        "app": "python3 app.py",
        "context": {
          "@aws-cdk/core:stackRelativeExports": true,
          "@aws-cdk/aws-lambda:recognizeLayerVersion": true
        }
      }
      ```

14. **No `.dockerignore` Files**
    - Neither `backend/` nor `frontend/` has a `.dockerignore` file. This means unnecessary files (`node_modules`, `__pycache__`, `.git`, test artifacts) may be sent to the Docker build context, slowing builds.
    - **Recommendation**: Add `.dockerignore` files to both directories.

15. **Frontend Deployment Relies on Pre-Built `dist/` Directory**
    - `frontend_stack.py` checks if `frontend/dist` exists and deploys it. If the developer hasn't run `npm run build` before `cdk deploy`, the assets are silently skipped.
    - **Recommendation**: Add a pre-deploy check or build step that runs `npm run build` before synthesis/deployment.

## Coverage Summary
- **Test command**: `cd infra/cdk && source /home/youri/Projects/Sources/.venv/bin/activate && python -m pytest tests/ -v`
- **Result**: **TIMEOUT** (3 tests collected, 1 passed, 2 timed out after 120s)
- **Coverage**: **N/A** (tests did not complete)
- **Target**: >= 80%
- **Untested critical paths**:
  - Backend stack synthesis with Lambda Layer bundling (Docker-based)
  - Frontend stack with S3 deployment
  - Cross-stack dependency wiring (data → backend → frontend)
  - IAM policy attachment validation
  - CloudFront error response configuration
  - API Gateway HTTP API integration

**Note**: The test structure is correct (uses `aws_cdk.assertions.Template`), but the `PythonLayerVersion` bundling triggers a full Docker build during synthesis, causing timeouts. This must be fixed before tests can serve as a CI gate.

## Score Breakdown
| Category               | Score (/10) |
|------------------------|-------------|
| Coding style           | 8           |
| Architecture           | 8           |
| Performance & readability | 7        |
| Tests & coverage       | 4           |

### Scoring Rationale
- **Coding style (8/10)**: Clean, well-organized CDK stacks. Good use of constructs, proper separation of concerns. Minor issues with inline JS function and missing stage-based naming.
- **Architecture (8/10)**: Excellent stack separation (data → backend → frontend). Proper cross-stack references. HTTP API Gateway is cost-effective. CloudFront + S3 for frontend is standard. Issues: no CI/CD, hardcoded CORS, missing production-ready Dockerfiles.
- **Performance & readability (7/10)**: Code is readable and well-structured. Lambda timeout could be tighter. Docker images carry unnecessary files. CDK tests need optimization.
- **Tests & coverage (4/10)**: Test structure exists and covers the right assertions, but they time out and cannot run in CI. This is a critical gap — tests that cannot execute provide no safety. CDK test coverage is effectively 0% until the timeout issue is resolved.

## Global Note: 6.8/10

The infrastructure is **well-architected** for an MVP with good stack separation, Free Tier awareness, and clean CDK patterns. The primary gaps are:
1. **No CI/CD automation** — everything is manual, which is the single biggest risk.
2. **CDK tests time out** — the test safety net exists on paper but cannot execute reliably.
3. **Dockerfiles are dev-only** — no production-ready container images exist.

These are all addressable and do not undermine the solid architectural foundation.

## Review Status
**CHANGES REQUIRED**

The infrastructure cannot be approved without:
1. A CI/CD pipeline (at minimum for testing and synthesis validation).
2. Fixing CDK test timeouts so they can serve as a quality gate.
3. Addressing the hardcoded CORS wildcard for non-dev environments.

## Recommended Next Actions

1. **[Critical] Add GitHub Actions CI workflow** (`.github/workflows/ci.yml`)
   - Backend: `pytest` with coverage >= 80%
   - Frontend: `npm run build`
   - CDK: `cdk synth` validation (skip full test if timeout persists, or fix timeout first)

2. **[Critical] Fix CDK test timeouts**
   - Mock `PythonLayerVersion` bundling to skip Docker during test synthesis
   - Add `pytest-timeout` with appropriate limits
   - Verify all 3 tests pass in CI

3. **[Critical] Harden Lambda admin auth fallback**
   - Ensure `ADMIN_PASSWORD` env var is set as a fallback in `backend_stack.py`, or document manual SSM parameter creation as a hard pre-deployment requirement

4. **[Major] Parameterize CORS origins**
   - Use `CORS_ALLOWED_ORIGINS: "*"` only for `dev` stage
   - For `prod`, derive from CloudFront distribution domain name

5. **[Major] Conditionally apply S3 removal policy**
   - Match `dynamodb_stack.py` pattern: `DESTROY` for `dev`, `RETAIN` for other stages

6. **[Major] Clean up backend Dockerfile**
   - Remove `tests/` and `pytest.ini` from production image
   - Add `.dockerignore` files to `backend/` and `frontend/`

7. **[Minor] Reduce Lambda timeout** from 30s to 10s

8. **[Minor] Extract CloudFront function to a file** instead of inline string

9. **[Minor] Add `npm run build` step** before CDK frontend deployment or add it as a pre-deploy script

10. **[Minor] Add CDK context/feature flags** to `cdk.json`
