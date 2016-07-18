import os

DEBUG = os.environ.get('DEBUG', True)
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/')
VOTEORG_PARTNER = os.environ.get('VOTEORG_PARTNER')
