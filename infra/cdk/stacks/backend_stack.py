from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack, aws_apigatewayv2_alpha as apigw, aws_apigatewayv2_integrations_alpha as integrations, aws_lambda as lambda_, aws_ssm as ssm
from aws_cdk.aws_lambda_python_alpha import PythonFunction
from constructs import Construct


class BackendStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        stage: str,
        dishes_table,
        members_table,
        votes_table,
        weekly_menus_table,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        admin_password_parameter = ssm.StringParameter(
            self,
            "AdminPasswordParameter",
            parameter_name=f"/family-meal-planner/{stage}/admin-password",
            string_value="CHANGEME",
            description="Admin password for the Family Meal Planner application",
            parameter_type=ssm.ParameterType.SECURE_STRING,
        )
        admin_password_parameter.apply_removal_policy(RemovalPolicy.DESTROY)

        self.backend_function = PythonFunction(
            self,
            "BackendFunction",
            entry="../../backend",
            index="app/lambda_handler.py",
            runtime=lambda_.Runtime.PYTHON_3_12,
            architecture=lambda_.Architecture.X86_64,
            timeout=Duration.seconds(30),
            environment={
                "DISHES_TABLE_NAME": dishes_table.table_name,
                "MEMBERS_TABLE_NAME": members_table.table_name,
                "VOTES_TABLE_NAME": votes_table.table_name,
                "WEEKLY_MENUS_TABLE_NAME": weekly_menus_table.table_name,
                "STAGE": stage,
                "BACKEND_PERSISTENCE_MODE": "dynamodb",
                "ADMIN_PASSWORD_PARAMETER_NAME": admin_password_parameter.parameter_name,
            },
        )

        admin_password_parameter.grant_read(self.backend_function)

        dishes_table.grant_read_write_data(self.backend_function)
        members_table.grant_read_write_data(self.backend_function)
        votes_table.grant_read_write_data(self.backend_function)
        weekly_menus_table.grant_read_write_data(self.backend_function)

        api = apigw.HttpApi(
            self,
            "BackendHttpApi",
            default_integration=integrations.HttpLambdaIntegration(
                "HttpApiIntegration",
                handler=self.backend_function,
            ),
            cors_preflight=apigw.CorsPreflightOptions(
                allow_origins=["*"]),
        )

        self.api_url = api.url

        CfnOutput(self, "BackendApiUrl", value=api.url)
        CfnOutput(self, "BackendFunctionName", value=self.backend_function.function_name)
