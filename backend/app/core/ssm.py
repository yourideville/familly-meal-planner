import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_admin_password(parameter_name: str) -> str:
    if not parameter_name:
        raise ValueError("ADMIN_PASSWORD_PARAMETER_name must be provided")

    logger.info("Loading admin password from SSM parameter: %s", parameter_name)
    ssm = boto3.client("ssm")
    try:
        response = ssm.get_parameter(Name=parameter_name)
        return response["Parameter"]["Value"]
    except ClientError as exc:
        raise RuntimeError(
            f"Unable to load admin password from SSM parameter '{parameter_name}': {exc}"
        ) from exc
