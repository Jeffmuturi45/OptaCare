from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Relax secure cookies for HTTP localhost
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Disable HSTS locally
SECURE_HSTS_SECONDS = 0

# Show emails in terminal
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Django debug toolbar (optional, install separately)
INTERNAL_IPS = ['127.0.0.1']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'INFO',  # set DEBUG to see all SQL
        },
    },
}
