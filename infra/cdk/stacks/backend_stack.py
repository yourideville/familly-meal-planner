from aws_cdk import CfnOutput, Duration, Stack, aws_apigatewayv2_alpha as apigw, aws_apigatewayv2_integrations_alpha as integrations, aws_iam as iam, aws_lambda as lambda_
from aws_cdk.aws_lambda_python_alpha import PythonLayerVersion, BundlingOptions
from constructs import Construct

ADMIN_PASSWORD_SSM_PATTERN = "/family-meal-planner/{stage}/admin-password"


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

        deps_layer = PythonLayerVersion(
            self,
            "BackendDepsLayer",
            entry="../../backend",
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_13],
            compatible_architectures=[lambda_.Architecture.ARM_64],
            bundling=BundlingOptions(
                platform="linux/arm64",
                environment={"PIP_ONLY_BINARY": ":all:"},
            ),
        )

        self.backend_function = lambda_.Function(
            self,
            "BackendFunction",
            code=lambda_.Code.from_asset(
                "../../backend",
                exclude=["tests", "pytest.ini", "requirements.txt", "Dockerfile", "__pycache__", "*.pyc"],
            ),
            handler="app.lambda_handler.handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            architecture=lambda_.Architecture.ARM_64,
            timeout=Duration.seconds(30),
            layers=[deps_layer],
            environment={
                "TABLE_NAME": table.table_name,
                "STAGE": stage,
                "BACKEND_PERSISTENCE_MODE": "dynamodb",
                "ADMIN_PASSWORD_PARAMETER_NAME": admin_password_parameter_name,
                "CORS_ALLOWED_ORIGINS": "*",
                "SECURE_COOKIE": "true",
                "COOKIE_SAMESITE": "none",
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
