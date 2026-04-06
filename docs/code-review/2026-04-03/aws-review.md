# AWS/DevOps Code Review — 2026-04-03

## Review Scope
- Scope: branch
- Files reviewed: 12
- Changed files:
  - `infra/cdk/app.py`
  - `infra/cdk/cdk.json`
  - `infra/cdk/requirements.txt`
  - `infra/cdk/stacks/__init__.py`
  - `infra/cdk/stacks/backend_stack.py`
  - `infra/cdk/stacks/dynamodb_stack.py`
  - `infra/cdk/stacks/frontend_stack.py`
  - `infra/cdk/tests/test_stacks.py`
  - `backend/Dockerfile`
  - `frontend/Dockerfile`
  - `docker-compose.yml`
  - `backend/app/core/ssm.py` (read for context)
  - `backend/app/core/auth.py` (read for context)

## Findings

### Critical

#### C1 — SSM SecureString creation not supported by CloudFormation/CDK

**File:** `infra/cdk/stacks/backend_stack.py` lines 22–30

```python
admin_password_parameter = ssm.StringParameter(
    self,
    "AdminPasswordParameter",
    parameter_name=f"/family-meal-planner/{stage}/admin-password",
    string_value="CHANGEME",
    description="Admin password for the Family Meal Planner application",
    parameter_type=ssm.ParameterType.SECURE_STRING,
)
```

**Problem:** CloudFormation — and by extension CDK — does **not** support creating `SecureString` SSM parameters. `AWS::SSM::Parameter` only supports `String` and `StringList` types. This will fail at deploy time with a CloudFormation error. Additionally, the plaintext default `"CHANGEME"` is embedded in the CDK code and would be visible in the CloudFormation template.

**Fix:** Either:
1. Provision the SecureString parameter out-of-band (AWS CLI/Console) and **reference** it via `ssm.StringParameter.from_secure_string_parameter_attributes()`, or
2. Replace with AWS Secrets Manager (`aws_secretsmanager.Secret`), which CDK fully supports for managing secrets.

---

#### C2 — SSM `get_parameter` missing `WithDecryption=True`

**File:** `backend/app/core/ssm.py` line 17

```python
response = ssm.get_parameter(Name=parameter_name)
```

**Problem:** For SecureString parameters, `get_parameter()` without `WithDecryption=True` returns the encrypted ciphertext, not the plaintext password. Authentication will never succeed because the comparison will be against an encrypted blob.

**Fix:** Change to:
```python
response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
```

> **Note:** This is application code (out of scope for infra changes), but it is a **deployment-blocking** bug that prevents the SSM integration from working.

---

#### C3 — CORS allows all origins (`*`)

**File:** `infra/cdk/stacks/backend_stack.py` line 67

```python
cors_preflight=apigw.CorsPreflightOptions(
    allow_origins=["*"]),
```

**Problem:** Wildcard origin in production allows any website to make authenticated API requests to the backend. This is a significant security risk for an app with admin auth.

**Fix:** Restrict to the CloudFront distribution domain or a known list of origins. Pass the frontend URL as a parameter:
```python
cors_preflight=apigw.CorsPreflightOptions(
    allow_origins=[f"https://{frontend_distribution_domain}"],
    allow_methods=[apigw.CorsHttpMethod.ANY],
    allow_headers=["Content-Type", "Authorization", "Cookie"],
)
```

---

### Major

#### M1 — FrontendStack raises `FileNotFoundError` at synth time

**File:** `infra/cdk/stacks/frontend_stack.py` lines 52–56

```python
if not frontend_dist.exists():
    raise FileNotFoundError(...)
```

**Problem:** This makes `cdk synth` fail unless `frontend/dist` has been pre-built. It also makes the CDK test `test_frontend_stack_creates_bucket_and_distribution` fail in CI unless a build step runs first. CDK synthesis should always succeed for template validation and testing.

**Fix:** Guard the `BucketDeployment` construct behind the existence check instead of raising:
```python
if frontend_dist.exists():
    s3_deployment.BucketDeployment(...)
else:
    import warnings
    warnings.warn(f"Frontend assets not found at {frontend_dist}. Skipping deployment asset upload.")
```

Or use a dummy empty directory during synth/test and rely on CI to build assets before `cdk deploy`.

---

#### M2 — `RemovalPolicy.DESTROY` on all DynamoDB tables

**File:** `infra/cdk/stacks/dynamodb_stack.py` line 20

```python
"removal_policy": RemovalPolicy.DESTROY,
```

**Problem:** All four tables will be permanently deleted on `cdk destroy`. This is acceptable for dev/test but dangerous for production. Data loss is irreversible.

**Fix:** Make the removal policy stage-dependent:
```python
removal_policy = RemovalPolicy.DESTROY if stage == "dev" else RemovalPolicy.RETAIN
```

---

#### M3 — No Point-in-Time Recovery (PITR) on DynamoDB tables

**File:** `infra/cdk/stacks/dynamodb_stack.py`

**Problem:** None of the 4 tables enable PITR. For production tables with user data (votes, menus), accidental deletes or overwrites cannot be recovered.

**Fix:** Add `point_in_time_recovery=True` for production stages at minimum.

---

#### M4 — Python version mismatch: Dockerfile (3.11) vs Lambda (3.13)

**Files:** `backend/Dockerfile` line 1 vs `infra/cdk/stacks/backend_stack.py` line 39

- Dockerfile: `FROM python:3.11-slim`
- CDK Lambda: `runtime=lambda_.Runtime.PYTHON_3_13`

**Problem:** Local development and testing run on Python 3.11, but the Lambda function uses Python 3.13. This can cause subtle compatibility differences between local and deployed behavior.

**Fix:** Align both to the same version. Update the Dockerfile to `python:3.13-slim`.

---

#### M5 — CORS missing `allow_methods` and `allow_headers`

**File:** `infra/cdk/stacks/backend_stack.py` line 67

**Problem:** Only `allow_origins` is specified. Without `allow_methods` and `allow_headers`, browsers may block preflight requests for non-simple methods (PUT, DELETE) or custom headers.

**Fix:** Add explicit method and header allowlists:
```python
cors_preflight=apigw.CorsPreflightOptions(
    allow_origins=[...],
    allow_methods=[apigw.CorsHttpMethod.ANY],
    allow_headers=["Content-Type", "Authorization", "Cookie"],
)
```

---

#### M6 — CloudFront OAI is legacy; use OAC

**File:** `infra/cdk/stacks/frontend_stack.py` lines 29–30

```python
origin_access_identity = cloudfront.OriginAccessIdentity(self, "FrontendOAI")
```

**Problem:** Origin Access Identity (OAI) is a legacy mechanism. AWS recommends Origin Access Control (OAC) for new deployments. OAC supports additional features (SSE-KMS, more S3 regions).

**Fix:** Replace with `S3BucketOrigin.with_origin_access_control()`:
```python
origin=origins.S3BucketOrigin.with_origin_access_control(self.bucket)
```

---

#### M7 — No CI/CD pipeline defined

**Problem:** No GitHub Actions workflows or other CI/CD configuration files exist in the repository. Infrastructure changes have no automated validation (synth, test, deploy) on push/PR.

**Fix:** Create `.github/workflows/cdk.yml` with at minimum:
1. `cdk synth` on every PR
2. `pytest infra/cdk/tests/` on every PR
3. `cdk deploy` on merge to main (with approval gate)

---

### Minor

#### m1 — `cdk.json` has no context or feature flags

**File:** `infra/cdk/cdk.json`

The file only contains `{"app": "python3 app.py"}`. Consider adding recommended CDK feature flags to opt into best practices:
```json
{
  "app": "python3 app.py",
  "context": {
    "@aws-cdk/aws-s3:serverAccessLogsUseBucketPolicy": true,
    "@aws-cdk/aws-cloudfront:defaultSecurityPolicyTLSv1.2_2021": true
  }
}
```

---

#### m2 — CDK alpha module dependencies

**File:** `infra/cdk/requirements.txt`

`aws-cdk.aws-lambda-python-alpha` and `aws-cdk.aws-apigatewayv2-integrations-alpha` are alpha modules with potential breaking changes on updates. Pin to specific versions or document the risk.

---

#### m3 — S3 bucket has no server access logging

**File:** `infra/cdk/stacks/frontend_stack.py`

The frontend S3 bucket has no access logging configured. For audit and security compliance, consider adding `server_access_logs_bucket` or using CloudFront access logs.

---

#### m4 — Docker Compose does not pin image versions for builds

**File:** `docker-compose.yml`

Both services use local Dockerfiles which is fine, but the compose file does not set `restart` policies or health checks. Minor for local dev.

---

#### m5 — CDK test assertions are shallow

**File:** `infra/cdk/tests/test_stacks.py`

Tests only verify resource counts. They don't validate:
- IAM policy statements (least privilege)
- Lambda environment variables
- DynamoDB table key schemas
- CORS configuration
- CloudFront viewer protocol policy

## Coverage Summary
- Test command: `pytest infra/cdk/tests/ -v`
- Result: **BLOCKED** — CDK dependencies could not be installed (proxy/network issue)
- Coverage: **Not measurable** (CDK deps unavailable)
- Untested critical paths:
  - IAM policy content (grant statements)
  - Lambda environment variables correctness
  - SSM parameter integration
  - CORS configuration
  - CloudFront security settings (TLS, viewer protocol)
  - Stage-dependent behavior (dev vs prod)
  - `FrontendStack` test likely fails due to `FileNotFoundError` when `frontend/dist` is absent

## Score Breakdown
| Category                  | Score (/10) |
|---------------------------|-------------|
| Coding style              | 8           |
| Architecture              | 7           |
| Performance & readability | 7           |
| Tests & coverage          | 4           |

## Global Note: 5/10

## Review Status
**CHANGES REQUIRED**

## Recommended Next Actions

1. **[Critical]** Replace SSM SecureString creation with Secrets Manager or out-of-band provisioning — current approach will fail at deploy time.
2. **[Critical]** Add `WithDecryption=True` to `ssm.get_parameter()` call in `backend/app/core/ssm.py`.
3. **[Critical]** Restrict CORS origins to the actual frontend domain instead of `*`.
4. **[Major]** Fix FrontendStack to not raise during synth/test when `frontend/dist` is absent.
5. **[Major]** Make `RemovalPolicy` stage-dependent (DESTROY for dev, RETAIN for prod).
6. **[Major]** Align Python versions between Dockerfile (3.11) and Lambda runtime (3.13).
7. **[Major]** Add `allow_methods` and `allow_headers` to CORS configuration.
8. **[Major]** Migrate from CloudFront OAI to OAC.
9. **[Major]** Create a CI/CD pipeline (GitHub Actions) for automated CDK synth, test, and deploy.
10. **[Minor]** Deepen CDK test assertions to cover IAM policies, environment variables, and security settings.
11. **[Minor]** Enable PITR on DynamoDB tables for production.
12. **[Minor]** Add CDK recommended feature flags to `cdk.json`.
