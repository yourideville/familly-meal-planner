from aws_cdk import RemovalPolicy, Stack, aws_dynamodb as dynamodb
from constructs import Construct


class DynamoDbStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        stage: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        table_props = {
            "billing_mode": dynamodb.BillingMode.PAY_PER_REQUEST,
            "removal_policy": RemovalPolicy.DESTROY,
        }

        self.dishes_table = dynamodb.Table(
            self,
            "DishesTable",
            table_name=f"MealPlanner-Dishes-{stage}",
            partition_key=dynamodb.Attribute(name="dish_id", type=dynamodb.AttributeType.STRING),
            **table_props,
        )

        self.members_table = dynamodb.Table(
            self,
            "MembersTable",
            table_name=f"MealPlanner-Members-{stage}",
            partition_key=dynamodb.Attribute(name="member_id", type=dynamodb.AttributeType.STRING),
            **table_props,
        )

        self.votes_table = dynamodb.Table(
            self,
            "VotesTable",
            table_name=f"MealPlanner-Votes-{stage}",
            partition_key=dynamodb.Attribute(name="vote_id", type=dynamodb.AttributeType.STRING),
            **table_props,
        )

        self.weekly_menus_table = dynamodb.Table(
            self,
            "WeeklyMenusTable",
            table_name=f"MealPlanner-WeeklyMenus-{stage}",
            partition_key=dynamodb.Attribute(name="week_id", type=dynamodb.AttributeType.STRING),
            **table_props,
        )
