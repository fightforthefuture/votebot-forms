from flask import Flask, make_response
from flask_rq2 import RQ

app = Flask('votebot-forms')
app.config.from_object('app.config')

rq = RQ()
rq.init_app(app)
print rq.module_path

# votebot views depend on rq for jobs, import after we've created it
from views import votebot
app.register_blueprint(votebot)


@app.route('/')
def index():
    return make_response('hello from votebot')
