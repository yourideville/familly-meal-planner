from aws_cdk import CfnOutput, Duration, Stack, aws_apigatewayv2_alpha as apigw, aws_apigatewayv2_integrations_alpha as integrations, aws_iam as iam, aws_lambda as lambda_
from aws_cdk.aws_lambda_python_alpha import PythonFunction
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

        self.backend_function = PythonFunction(
            self,
            "BackendFunction",
            entry="../../backend",
            index="app/lambda_handler.py",
            runtime=lambda_.Runtime.PYTHON_3_13,
            architecture=lambda_.Architecture.X86_64,
            timeout=Duration.seconds(30),
            environment={
                "TABLE_NAME": table.table_name,
                "STAGE": stage,
                "BACKEND_PERSISTENCE_MODE": "dynamodb",
                "ADMIN_PASSWORD_PARAMETER_NAME": admin_password_parameter_name,
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
            cors_preflight=apigw.CorsPreflightOptions(
                allow_origins=["*"],
                allow_methods=[apigw.CorsHttpMethod.ANY],
                allow_headers=["Content-Type", "Authorization", "Cookie"],
            ),
        )

        self.api_url = api.url

        CfnOutput(self, "BackendApiUrl", value=api.url)
        CfnOutput(self, "BackendFunctionName", value=self.backend_function.function_name)
