from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

def send_verification_email(user: User) -> None:
    """
    Build and send a one-time verification email to user
    """
    if user.is_active:
        raise ValueError("Account is already verified.")

    # Change the login timestamp to invalidate the previous link
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = f"{settings.FRONTEND_URL}/verify-email?uid={uid}&token={token}"
    html = render_to_string("verify.html", {"first_name": user.first_name, "link": link})
    send_mail(
        subject="Confirmation Email",
        message="",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html,
        fail_silently=False,
    )
