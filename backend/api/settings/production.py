import environ

from .base import *

DEBUG = False

# Force HTTPS
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True

# Enable HSTS
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

env = environ.Env(
    REDIS_URL=(str, "redis://127.0.0.1:6379/1"),
    SECRET_KEY=(str),
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)
