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

# Email
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'you@gmail.com'
# EMAIL_HOST_PASSWORD = 'your-app-password'

env = environ.Env(
    REDIS_URL=(str, "redis://127.0.0.1:6379/1"),
    SECRET_KEY=(str),
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)
