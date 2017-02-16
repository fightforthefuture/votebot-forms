from flask import Flask, make_response
from flask_rq2 import RQ

import logging

app = Flask('app')
app.config.from_object('app.config')

rq = RQ(async=app.config.get('DEBUG', False))
rq.init_app(app)

if app.config.get('DEBUG'):
	loglevel = logging.DEBUG
else:
	loglevel = logging.WARNING
logging.basicConfig(level=loglevel)

# votebot views depend on rq & db for jobs, import after we've created them
from views import votebot
app.register_blueprint(votebot)


@app.route('/')
def index():
    return make_response('hello from votebot')