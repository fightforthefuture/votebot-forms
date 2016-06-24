from flask import Flask, make_response
from views import votebot

app = Flask(__name__)
app.config.from_object('app.config')
app.register_blueprint(votebot)


@app.route('/')
def index():
    return make_response('hello from votebot')
