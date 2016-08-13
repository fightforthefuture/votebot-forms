from flask import jsonify
import requests
from .app import rq, db


@rq.job
def submit_form(form, user, callback_url):
    status = form.submit(user)

    # log form.browser final state, so we can determine sucess or error strings
    db.log_response(form, status)

    if callback_url:
        requests.post(callback_url, status)
    return jsonify(status)


@rq.job
def get_pdf(form, user, callback_url):
    status = form.get_download(user)
    if callback_url:
        requests.post(callback_url, status)
    return jsonify(status)
