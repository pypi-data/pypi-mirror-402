"""Email tools for Pydantic AI agents.

This module provides tools for sending emails via Django's email backend.
"""

from django.conf import settings
from django.core.mail import send_mail
from pydantic_ai.toolsets import FunctionToolset


async def send_email(email: str, subject: str, body: str) -> bool:
    """Send an email to a recipient.

    Args:
        email: The email address of the recipient.
        subject: The subject of the email.
        body: The body of the email.

    Returns:
        True if email was sent successfully.
    """
    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
    return True


email_toolset = FunctionToolset(tools=[send_email])
