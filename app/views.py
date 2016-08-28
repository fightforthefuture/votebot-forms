from flask import Blueprint, request, jsonify, current_app
from ovr_forms import OVR_FORMS
from ovr_forms.base_ovr_form import OVRError
from ovr_forms.form_utils import clean_sensitive_info, ValidationError
import jobs

votebot = Blueprint('votebot', __name__)


@votebot.errorhandler(OVRError)
def handle_ovr_error(error):
    error_dict = error.to_dict()
    return render_error(
        error.status_code,
        "form_error",
        error_dict["message"],
        error_dict["payload"]
    )

def render_error(status_code, str_code, message=None, payload=None):
    response = jsonify({
            "error": True,
            "status_code": status_code,
            "error_type": str_code,
            "message": message,
            "payload": payload
        })
    response.status_code = status_code
    return response

@votebot.route('/generate_pdf', methods=['POST'])
def vote_dot_org():
    return registration(request, "generate_pdf")


@votebot.route('/ovr', methods=['POST'])
def ovr():
    return registration(request, "ovr")


def registration(request, registration_type="generate_pdf"):
    request_json = request.get_json(force=True)  # so we don't have to set mimetype
    if not "user" in request_json:
        return render_error(400, "missing_user_data", "No user data specified.")

    user = request_json['user']

    # pull fields out of user.settings
    if 'settings' in user:
        for (key, value) in user['settings'].items():
            user[key] = value
        del user['settings']

    state = user['state']
    if registration_type == "generate_pdf":
        form = OVR_FORMS['default']()
    elif state in OVR_FORMS:
        form = OVR_FORMS[state]()
    else:
        return render_error(
            500,
            "internal_error",
            "OVR submission specified, but state not implemented."
        )

    # validate before queueing for submission
    try:
        form.validate(user)
    except ValidationError, e:
        if hasattr(current_app, 'sentry'):
            current_app.sentry.captureException(e)
            user_filtered = clean_sensitive_info(user)
            current_app.sentry.user_context(user_filtered)
        return render_error(400, "missing_fields", "Missing required fields", e.payload)

    # for local development / testing.
    synchronous_submit = current_app.config.get('SYNCHRONOUS_SUBMIT', False)
    if synchronous_submit == False or synchronous_submit == 'False':
        return jobs.submit_form(form, user, callback_url=request_json.get('callback_url'))

    else:
        # queue form submission and success callback
        jobs.submit_form.queue(form, user, callback_url=request_json.get('callback_url'))

        # if form.__class__.__name__ is 'VoteDotOrg':
            # create new job for pdf check
            # TODO delay a few seconds?
            # TODO retry automatically if failed?
            # jobs.get_pdf.queue(form, user, callback_url=request_json.get('callback_url'))
            # jobs.get_pdf.queue(form, user, callback_url=None)

        return jsonify({
            'status': 'queued',
            'uid': str(form.get_uid())
        })


@votebot.route('/confirm')
def confirm(user):
    # status = send_email(confirmation, user)
    return jsonify({'status': True})
