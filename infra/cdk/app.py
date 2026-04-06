#!/usr/bin/env python3
import os

from aws_cdk import App, Environment

from stacks.backend_stack import BackendStack
from stacks.dynamodb_stack import DynamoDbStack
from stacks.frontend_stack import FrontendStack

app = App()
stage = os.getenv("CDK_STAGE", "dev")
env = Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=os.getenv("CDK_DEFAULT_REGION"),
)

data_stack = DynamoDbStack(
    app,
    f"meal-planner-data-{stage}",
    stage=stage,
    env=env,
)

backend_stack = BackendStack(
    app,
    f"meal-planner-backend-{stage}",
    stage=stage,
    table=data_stack.table,
    env=env,
)

FrontendStack(
    app,
    f"meal-planner-frontend-{stage}",
    stage=stage,
    api_url=backend_stack.api_url,
    env=env,
)

app.synth()
