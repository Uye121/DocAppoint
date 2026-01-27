import jwt
import time
import uuid
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


def build_verification_jwt(user) -> str:
    now = int(time.time())
    payload = {
        "uid": str(user.pk),
        "act": "verify_email",
        "iat": now,
        "exp": now + 30 * 60,  # 30-min clock expiry
        "jti": str(uuid.uuid4()),  # unique id for this token
        "ts": int(user.reset_sent_at.timestamp()) if user.reset_sent_at else now,
    }
    return jwt.encode(
        payload,
        settings.EMAIL_VERIFY_SECRET,
        algorithm="HS256",
    )


def check_verification_jwt(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.EMAIL_VERIFY_SECRET,
            algorithms=["HS256"],
            options={"require": ["exp", "act", "uid", "ts"]},
        )
        if payload.get("act") != "verify_email":
            raise jwt.InvalidTokenError
        user = User.objects.get(pk=payload["uid"])

        # Invalidate older tokens
        if user.reset_sent_at:
            latest_ts = int(user.reset_sent_at.timestamp())
            if payload["ts"] < latest_ts:
                return None

        return str(user.pk)
    except (jwt.InvalidTokenError, User.DoesNotExist):
        return None
