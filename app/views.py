from flask import Blueprint, request, jsonify
from ovr_forms import OVR_FORMS
from ovr_forms.base_ovr_form import OVRError

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
    state = user['state']

    if state in OVR_FORMS:
        form = OVR_FORMS[state]()
    else:
        form = OVR_FORMS['default']()

    status = form.submit(user)

    return jsonify(status)


@votebot.route('/confirm')
def confirm(user):
    # status = send_email(confirmation, user)
    return jsonify({'status': True})
