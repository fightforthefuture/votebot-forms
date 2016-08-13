from flask import Blueprint, request, jsonify, current_app
from ovr_forms import OVR_FORMS
from ovr_forms.base_ovr_form import OVRError
from ovr_forms.form_utils import clean_sensitive_info
import jobs

votebot = Blueprint('votebot', __name__)


@votebot.errorhandler(OVRError)
def handle_ovr_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@votebot.route('/registration', methods=['POST'])
def registration():
    request_json = request.get_json(force=True)  # so we don't have to set mimetype
    user = request_json['user']
    if not user:
        return jsonify({'status': 'no user data specified'})

    # pull fields out of user.settings
    if 'settings' in user:
        for (key, value) in user['settings'].items():
            user[key] = value
        del user['settings']

    state = user['state']
    if state in OVR_FORMS:
        form = OVR_FORMS[state]()
    else:
        form = OVR_FORMS['default'](current_app.config.get('VOTEORG_PARTNER'))

    # validate before queueing for submission
    try:
        form.validate(user)
    except OVRError, e:
        if hasattr(current_app, 'sentry'):
            current_app.sentry.captureException(e)
            user_filtered = clean_sensitive_info(user)
            current_app.sentry.user_context(user_filtered)
        return jsonify({'status': 'error', 'errors': e.to_dict()})

    # for local development / testing.
    if current_app.config.get('SYNCHRONOUS_SUBMIT', False):
        return jobs.submit_form(form, user, callback_url=request_json.get('callback_url'))

    else:
        # queue form submission and success callback
        jobs.submit_form.queue(form, user, callback_url=request_json.get('callback_url'))

        if form.__class__.__name__ is 'VoteDotOrg':
            # create new job for pdf check
            # TODO delay a few seconds?
            # TODO retry automatically if failed?
            jobs.get_pdf.queue(form, user, callback_url=request_json.get('callback_url'))

        return jsonify({'status': 'queued'})


@votebot.route('/confirm')
def confirm(user):
    # status = send_email(confirmation, user)
    return jsonify({'status': True})
