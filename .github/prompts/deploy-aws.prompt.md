## Name
Deploy Family Meal Planner to AWS

## Description
Plan and implement AWS deployment infrastructure for the Family Meal Planner application using CDK and CloudFront. The prompt focuses on creating deployable stacks, respecting workspace architecture boundaries, and keeping backend tests offline.

## Parameters
- **deploymentTarget** (string, optional): The target platform or service, e.g. `aws`, `cloudfront`, `lambda`, `dynamodb`.
- **scope** (string, optional): One of `infra`, `backend`, `frontend`, or `fullstack`.
- **constraints** (string, optional): Additional deployment requirements such as `CloudFront first`, `split stacks`, `offline backend tests`, or `no database persistence`.

## Command
1. Review the repo deployment plan and current infrastructure folders.
2. Determine the proper stack boundaries for AWS deployment, favoring separated stacks for CloudFront, backend Lambda/API, and supporting resources.
3. Create or update CDK app files, requirements, and tests without changing the offline backend test behavior.
4. Keep code architecture compliant with repository conventions and existing FastAPI/React structure.
5. Ensure deployment artifacts are coherent, documented, and ready for `cdk synth` / `cdk deploy`.

## Output format
- Summary of deployment scope
- Key files created or changed
- Stack boundaries and AWS services used
- Testing and offline constraints
- Next deployment steps

## Example invocation
`/deploy-aws deploymentTarget=aws scope=infra constraints="CloudFront first, split stacks, offline backend tests"`