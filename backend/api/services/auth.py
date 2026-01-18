from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import AbstractUser

from ..utils.tokens import build_verification_jwt

def send_verification_email(user: AbstractUser) -> None:
    """
    Build and send a one-time verification email to user
    """
    if user.is_active:
        raise ValueError("Account is already verified.")

    user.reset_sent_at = timezone.now()
    user.save(update_fields=["reset_sent_at"])

    token = build_verification_jwt(user)
    link = f"{settings.FRONTEND_URL}/verify-email?token={token}"

    html = render_to_string(
        "verify.html",
        {"first_name": user.first_name, "link": link}
    )

    send_mail(
        subject="Confirmation Email",
        message="",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html,
        fail_silently=False,
    )
