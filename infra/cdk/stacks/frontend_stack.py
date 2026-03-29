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

        origin_access_identity = cloudfront.OriginAccessIdentity(self, "FrontendOAI")
        self.bucket.grant_read(origin_access_identity)

        distribution = cloudfront.Distribution(
            self,
            "FrontendDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(self.bucket, origin_access_identity=origin_access_identity),
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
        if not frontend_dist.exists():
            raise FileNotFoundError(
                f"Frontend assets not found at {frontend_dist}. Run `npm --prefix ../../frontend run build` before deploying.`"
            )

        s3_deployment.BucketDeployment(
            self,
            "FrontendAssetDeployment",
            destination_bucket=self.bucket,
            sources=[s3_deployment.Source.asset(str(frontend_dist))],
            distribution=distribution,
            distribution_paths=["/*"],
        )

        CfnOutput(self, "FrontendBucketName", value=self.bucket.bucket_name)
        CfnOutput(self, "FrontendUrl", value=distribution.distribution_domain_name)
        CfnOutput(self, "BackendApiUrlForFrontend", value=api_url)
