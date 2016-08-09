import os

DEBUG = os.environ.get('DEBUG', True)
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/')
RQ_REDIS_URL = REDIS_URL

SENTRY_DSN = os.environ.get('SENTRY_DSN')

SMARTY_STREETS_AUTH_ID = os.environ.get('SMARTY_STREETS_AUTH_ID')
SMARTY_STREETS_AUTH_TOKEN = os.environ.get('SMARTY_STREETS_AUTH_TOKEN')

VOTEORG_PARTNER = os.environ.get('VOTEORG_PARTNER')
