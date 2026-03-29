import aws_cdk as cdk
from aws_cdk.assertions import Template

from stacks.backend_stack import BackendStack
from stacks.dynamodb_stack import DynamoDbStack
from stacks.frontend_stack import FrontendStack


def test_dynamodb_stack_creates_four_tables():
    app = cdk.App()
    stack = DynamoDbStack(app, "TestDataStack", stage="test")
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::DynamoDB::Table", 4)
    template.has_resource_properties(
        "AWS::DynamoDB::Table",
        {"BillingMode": "PAY_PER_REQUEST"},
    )


def test_backend_stack_creates_lambda_and_http_api():
    app = cdk.App()
    data_stack = DynamoDbStack(app, "TestDataStack", stage="test")
    stack = BackendStack(
        app,
        "TestBackendStack",
        stage="test",
        dishes_table=data_stack.dishes_table,
        members_table=data_stack.members_table,
        votes_table=data_stack.votes_table,
        weekly_menus_table=data_stack.weekly_menus_table,
    )
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::Lambda::Function", 1)
    template.resource_count_is("AWS::ApiGatewayV2::Api", 1)
    template.resource_count_is("AWS::IAM::Policy", 1)


def test_frontend_stack_creates_bucket_and_distribution():
    app = cdk.App()
    stack = FrontendStack(
        app,
        "TestFrontendStack",
        stage="test",
        api_url="https://example.com",
    )
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::S3::Bucket", 1)
    template.resource_count_is("AWS::CloudFront::Distribution", 1)
