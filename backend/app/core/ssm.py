import logging

logger = logging.getLogger(__name__)


def get_admin_password(parameter_name: str) -> str | None:
    if not parameter_name:
        raise ValueError("ADMIN_PASSWORD_PARAMETER_NAME must be provided")

    import boto3
    from botocore.exceptions import ClientError

    logger.info("Loading admin password from SSM parameter: %s", parameter_name)
    ssm = boto3.client("ssm")
    try:
        response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
        return response["Parameter"]["Value"]
    except ClientError as exc:
        logger.warning(
            "Unable to load admin password from SSM parameter '%s': %s. "
            "Falling back to ADMIN_PASSWORD env var.",
            parameter_name,
            exc,
        )
        return None
