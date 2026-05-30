"""
Email utility — password reset link delivery.

In development (APP_ENV=development):
  - Logs the reset URL to stdout and structlog. No SES call.
  - This means you don't need AWS credentials locally.

In staging/production:
  - Sends via AWS SES.
  - Requires: aws_access_key_id, aws_secret_access_key, aws_ses_region in settings.
  - The sender address "noreply@yusitime.com" must be verified in SES.
"""

import structlog
from app.core.config import get_settings

logger = structlog.get_logger()


async def send_reset_email(to_email: str, token: str) -> None:
    """
    Send a password reset link to the given email address.
    The token is the raw secrets.token_urlsafe(32) value — never log it in production.
    """
    settings = get_settings()
    reset_url = f"{settings.frontend_url}/reset-password?token={token}"

    if settings.app_env == "development":
        # Development: print to console so devs can click the link without SES
        logger.info("PASSWORD_RESET_LINK", email=to_email, url=reset_url)
        print(f"\n🔗 PASSWORD RESET LINK: {reset_url}\n")
        return

    # Production / Staging: send via AWS SES
    import boto3

    ses = boto3.client(
        "ses",
        region_name=settings.aws_ses_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )
    ses.send_email(
        Source="noreply@yusitime.com",
        Destination={"ToAddresses": [to_email]},
        Message={
            "Subject": {"Data": "Reset your Yusi Time password"},
            "Body": {
                "Text": {
                    "Data": (
                        f"Click the link below to reset your Yusi Time password.\n\n"
                        f"{reset_url}\n\n"
                        f"This link expires in 1 hour. If you did not request a reset, "
                        f"ignore this email — your password will not change."
                    )
                }
            },
        },
    )
    logger.info("PASSWORD_RESET_EMAIL_SENT", email=to_email)
