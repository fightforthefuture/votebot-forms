import os

DEBUG = os.environ.get('DEBUG', True)
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/')
RQ_REDIS_URL = REDIS_URL

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgres://localhost:5432/votebot-forms')

AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')

SENTRY_DSN = os.environ.get('SENTRY_DSN')
RAVEN_IGNORE_EXCEPTIONS = ['OVRError', 'ValidationError']
# only log internal issues to Sentry, OVRErrors are sent back to Mothership

SMARTY_STREETS_AUTH_ID = os.environ.get('SMARTY_STREETS_AUTH_ID')
SMARTY_STREETS_AUTH_TOKEN = os.environ.get('SMARTY_STREETS_AUTH_TOKEN')

VOTEORG_PARTNER = os.environ.get('VOTEORG_PARTNER')

PRESERVE_CONTEXT_ON_EXCEPTION = False

DEBUG_SUBMIT = bool(os.environ.get('DEBUG_SUBMIT', None))
# forces OVR form submission to occur synchronously, instead of queueing via redis
