from pathlib import Path

from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack, aws_cloudfront as cloudfront, aws_cloudfront_origins as origins, aws_s3 as s3, aws_s3_deployment as s3_deployment
from constructs import Construct


class FrontendStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        stage: str,
        api_url: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.bucket = s3.Bucket(
            self,
            "FrontendBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        distribution = cloudfront.Distribution(
            self,
            "FrontendDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(self.bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            default_root_object="index.html",
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(30),
                )
            ],
        )

        frontend_dist = Path(__file__).resolve().parent.parent / ".." / ".." / "frontend" / "dist"
        frontend_dist = frontend_dist.resolve()
        if frontend_dist.exists():
            s3_deployment.BucketDeployment(
                self,
                "FrontendAssetDeployment",
                destination_bucket=self.bucket,
                sources=[s3_deployment.Source.asset(str(frontend_dist))],
                distribution=distribution,
                distribution_paths=["/*"],
            )

        CfnOutput(self, "FrontendBucketName", value=self.bucket.bucket_name)
        CfnOutput(self, "FrontendUrl", value=f"https://{distribution.distribution_domain_name}")
        CfnOutput(self, "BackendApiUrlForFrontend", value=api_url)
