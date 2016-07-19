from flask import Blueprint, request, jsonify, current_app
from ovr_forms import OVR_FORMS
from ovr_forms.base_ovr_form import OVRError
import jobs

votebot = Blueprint('votebot', __name__)


@votebot.errorhandler(OVRError)
def handle_ovr_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@votebot.route('/registration', methods=['POST'])
def registration():
    user = request.get_json(force=True)  # so we don't have to set mimetype
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
        form = OVR_FORMS['default'](current_app.config.VOTEORG_PARTNER)
    jobs.submit_form.queue(form, user)  # needs to be a separate function, so we can queue execution
    return jsonify({'status': 'queued'})


@votebot.route('/confirm')
def confirm(user):
    # status = send_email(confirmation, user)
    return jsonify({'status': True})
