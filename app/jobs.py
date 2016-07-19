from flask import jsonify
import requests
from .app import rq


@rq.job
def submit_form(form, user, callback_url):
    status = form.submit(user)
    if callback_url:
        requests.post(callback_url, jsonify(status))
    return jsonify(status)
