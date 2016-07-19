from flask import jsonify
from .app import rq


@rq.job
def submit_form(form, user):
    status = form.submit(user)
    return jsonify(status)
