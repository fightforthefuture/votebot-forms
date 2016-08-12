from flask import Flask, make_response
from flask_rq2 import RQ
import db

app = Flask('votebot-forms')
app.config.from_object('app.config')

rq = RQ(async=app.config.get('DEBUG', False))
rq.init_app(app)

db.init_db(app)

# votebot views depend on rq & db for jobs, import after we've created them
from views import votebot
app.register_blueprint(votebot)


@app.route('/')
def index():
    return make_response('hello from votebot')


@app.teardown_appcontext
def close_app(error):
    """Close the database and deallocate prepared statements at the end of the request."""
    if hasattr(app, 'db'):
        app.db.close()
