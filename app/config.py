import os

DEBUG = os.environ.get('DEBUG', True)
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/')

# todo: take this out of source.
SMARTY_STREETS_AUTH_ID      = os.environ.get('SMARTY_STREETS_AUTH_ID', 'ef4709fd-662d-f40c-2cef-eab63b665ece')
SMARTY_STREETS_AUTH_TOKEN   = os.environ.get('SMARTY_STREETS_AUTH_TOKEN', 'KkA7ygaV4duTd1nryfDQ')