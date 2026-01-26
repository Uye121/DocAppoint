from .base import *  # noqa: F403

DEBUG = True

# Print email instead of send
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Pause ssecure cookies in development
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
