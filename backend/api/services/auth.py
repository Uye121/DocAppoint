import logging
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from typing import TYPE_CHECKING

from ..utils.tokens import build_verification_jwt

if TYPE_CHECKING:
    from api.models import User
else:
    from django.contrib.auth import get_user_model

    User = get_user_model()

logger = logging.getLogger(__name__)

def send_verification_email(user: User) -> None:
    """
    Build and send a one-time verification email to user
    """
    if user.is_active:
        logger.warning(f"Attempted to send verification email to already active user: {user.email}")
        return

    user.reset_sent_at = timezone.now()
    user.save(update_fields=["reset_sent_at"])

    token = build_verification_jwt(user)
    link = f"{settings.FRONTEND_URL}/verify-email?token={token}"

    html = render_to_string(
        "verify.html", {"first_name": user.first_name, "link": link, "expiry": 30}
    )
    plain_message = render_to_string(
        "verify.txt", {"first_name": user.first_name, "link": link, "expiry": 30}
    )

    send_mail(
        subject="Confirmation Email",
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html,
        fail_silently=False,
    )
