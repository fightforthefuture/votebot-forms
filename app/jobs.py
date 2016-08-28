from flask import jsonify
import requests
from .app import rq
from db import log_response


@rq.job
def submit_form(form, user, callback_url=None):
    status = form.submit(user, callback_url)

    status["form_class"] = form.__class__.__name__

    # log form.browser final state, so we can determine sucess or error strings
    log_id = log_response(form, status)

    status["reference"] = log_id
    status["uid"] = str(form.get_uid())

    if callback_url:
        requests.post(callback_url, status)
    return jsonify(status)


@rq.job
def get_pdf(form, user, callback_url=None):
    status = form.get_download(user)
    if callback_url:
        requests.post(callback_url, status)
    return jsonify(status)
