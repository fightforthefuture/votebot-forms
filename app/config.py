import os

DEBUG = os.environ.get('DEBUG', True)
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/')
RQ_REDIS_URL = REDIS_URL

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgres://localhost:5432/votebot-forms')

SENTRY_DSN = os.environ.get('SENTRY_DSN')

SMARTY_STREETS_AUTH_ID = os.environ.get('SMARTY_STREETS_AUTH_ID')
SMARTY_STREETS_AUTH_TOKEN = os.environ.get('SMARTY_STREETS_AUTH_TOKEN')

VOTEORG_PARTNER = os.environ.get('VOTEORG_PARTNER')

PRESERVE_CONTEXT_ON_EXCEPTION = False

SYNCHRONOUS_SUBMIT = bool(os.environ.get('SYNCHRONOUS_SUBMIT', None))