from pathlib import Path

from aws_cdk import CfnOutput, Duration, Fn, RemovalPolicy, Stack, aws_cloudfront as cloudfront, aws_cloudfront_origins as origins, aws_s3 as s3, aws_s3_deployment as s3_deployment
from constructs import Construct

_STRIP_API_PREFIX_JS = """\
function handler(event) {
    var request = event.request;
    var uri = request.uri;
    if (uri.indexOf('/api') === 0) {
        uri = uri.slice(4);
    }
    if (uri === '' || uri.charAt(0) !== '/') {
        uri = '/';
    }
    request.uri = uri;
    return request;
}
"""


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

        strip_api_prefix_fn = cloudfront.Function(
            self,
            "StripApiPrefixFunction",
            code=cloudfront.FunctionCode.from_inline(_STRIP_API_PREFIX_JS),
            comment="Strip /api prefix before forwarding to API Gateway",
        )

        api_domain = Fn.select(2, Fn.split("/", api_url))
        api_origin = origins.HttpOrigin(
            api_domain,
            protocol_policy=cloudfront.OriginProtocolPolicy.HTTPS_ONLY,
        )

        distribution = cloudfront.Distribution(
            self,
            "FrontendDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(self.bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            additional_behaviors={
                "/api/*": cloudfront.BehaviorOptions(
                    origin=api_origin,
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.HTTPS_ONLY,
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
                    function_associations=[
                        cloudfront.FunctionAssociation(
                            function=strip_api_prefix_fn,
                            event_type=cloudfront.FunctionEventType.VIEWER_REQUEST,
                        )
                    ],
                ),
            },
            default_root_object="index.html",
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(30),
                ),
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(30),
                ),
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
