from .base import *  # noqa: F403

DEBUG = True

# Print email instead of send
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
