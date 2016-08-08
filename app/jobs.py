from flask import jsonify
import requests
from .app import rq


@rq.job
def submit_form(form, user, callback_url):
    status = form.submit(user)

    if form.__class__.__name__ is 'VoteDotOrg':
        # create new job for pdf check
        # delay a few seconds?
        get_pdf.queue(form, user, callback_url)

    if callback_url:
        requests.post(callback_url, jsonify(status))
    return jsonify(status)


@rq.job
def get_pdf(form, user, callback_url):
    status = form.get_download(user)
    if callback_url:
        requests.post(callback_url, jsonify(status))
    return jsonify(status)
