from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack, aws_apigatewayv2_alpha as apigw, aws_apigatewayv2_integrations_alpha as integrations, aws_iam as iam, aws_lambda as lambda_, aws_logs as logs
from aws_cdk.aws_lambda_python_alpha import PythonLayerVersion, BundlingOptions
from constructs import Construct

ADMIN_PASSWORD_SSM_PATTERN = "/family-meal-planner/{stage}/admin-password"

# CORS origins by stage - use specific origins for non-dev stages
CORS_ORIGINS_BY_STAGE = {
    "dev": "*",  # Allow all for local development
    # Add production origins here when ready:
    # "prod": "https://your-cloudfront-domain.cloudfront.net",
}


class BackendStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        stage: str,
        table,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        admin_password_parameter_name = ADMIN_PASSWORD_SSM_PATTERN.format(stage=stage)

        # Get CORS origins for this stage, default to "*" if not configured
        cors_origins = CORS_ORIGINS_BY_STAGE.get(stage, "*")

        deps_layer = PythonLayerVersion(
            self,
            f"BackendDepsLayer-{stage}",  # Include stage in name for isolation
            entry="../../backend",
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_13],
            compatible_architectures=[lambda_.Architecture.ARM_64],
            bundling=BundlingOptions(
                platform="linux/arm64",
                environment={"PIP_ONLY_BINARY": ":all:"},
            ),
        )

        # Explicit CloudWatch LogGroup with 7-day retention
        log_group = logs.LogGroup(
            self,
            "BackendFunctionLogGroup",
            log_group_name=f"/aws/lambda/BackendFunction-{stage}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        self.backend_function = lambda_.Function(
            self,
            "BackendFunction",
            function_name=f"BackendFunction-{stage}",
            code=lambda_.Code.from_asset(
                "../../backend",
                exclude=["tests", "pytest.ini", "requirements.txt", "Dockerfile", "__pycache__", "*.pyc"],
            ),
            handler="app.lambda_handler.handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            architecture=lambda_.Architecture.ARM_64,
            timeout=Duration.seconds(45),
            layers=[deps_layer],
            log_group=log_group,
            environment={
                "TABLE_NAME": table.table_name,
                "STAGE": stage,
                "BACKEND_PERSISTENCE_MODE": "dynamodb",
                "ADMIN_PASSWORD_PARAMETER_NAME": admin_password_parameter_name,
                "ADMIN_PASSWORD": "CHANGEME",  # Fallback for bootstrapping - should be updated in SSM
                "CORS_ALLOWED_ORIGINS": cors_origins,
                "SECURE_COOKIE": "true",
                "COOKIE_SAMESITE": "none",
                "POWERTOOLS_SERVICE_NAME": f"family-meal-planner-{stage}",
                "POWERTOOLS_LOG_LEVEL": "INFO",
            },
        )

        self.backend_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=[
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter{admin_password_parameter_name}",
                ],
            )
        )

        table.grant_read_write_data(self.backend_function)

        api = apigw.HttpApi(
            self,
            "BackendHttpApi",
            default_integration=integrations.HttpLambdaIntegration(
                "HttpApiIntegration",
                handler=self.backend_function,
            ),
        )

        self.api_url = api.url

        CfnOutput(self, "BackendApiUrl", value=api.url)
        CfnOutput(self, "BackendFunctionName", value=self.backend_function.function_name)
