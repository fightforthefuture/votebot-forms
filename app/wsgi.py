# TODO, figure out how to load gevent monkey patch cleanly in production
try:
    from gevent.monkey import patch_all
    patch_all()
except ImportError:
    print "unable to apply gevent monkey.patch_all"

from app import app as application

if application.config.get('SENTRY_DSN'):
    from raven.contrib.flask import Sentry
    sentry = Sentry(application, dsn=application.config.get('SENTRY_DSN'))

from werkzeug.contrib.fixers import ProxyFix
application.wsgi_app = ProxyFix(application.wsgi_app)
