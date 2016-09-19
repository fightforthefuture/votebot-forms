from robobrowser import RoboBrowser
import json
from ..db import log_response
from form_utils import ValidationError
import requests
import uuid
import os


BASE_REQUIRED_FIELDS = [
    'first_name',
    'last_name',
    'state',
    'date_of_birth',
    'address',
    'city',
    'zip',
    'us_citizen',
    'state_id_number'
]


class BaseOVRForm(object):

    error_callback_url = None

    def __init__(self, start_url=None):
        self.user_agent = os.environ.get('USER_AGENT', 'votebot-forms')
        self.browser = RoboBrowser(parser='html.parser', user_agent=self.user_agent, history=True)
        # TESTING, disable SSL cert validation
        # self.browser.session.verify = 'charles-ssl-proxying-certificate.pem'

        if start_url:
            self.browser.open(start_url)
        self.required_fields = BASE_REQUIRED_FIELDS
        self.uid = uuid.uuid4()
        self.errors = []

    def get_uid(self):
        return self.uid

    def add_error(self, message, field='error'):
        self.errors.append({field: message})

    def add_required_fields(self, fields):
        # moving this to its own method seemed to remedy some object-reuse issues
        # I ran into with nose. todo: understand why those were popping up
        # and make sure this doesn't have any unintended consequences
        self.required_fields = self.required_fields + fields

    def check_required_fields(self, user):
        for field in self.required_fields:
            # if field not in user:
            if field not in user or user[field] == None:
                self.add_error('%s is required' % field.replace('_', ' '), field=field)

    def set_user_agent(self, user):
        self.browser.user_agent = '%s on behalf of %s %s' % (self.user_agent, user.get('first_name'), user.get('last_name'))

    def validate(self, user):
        self.check_required_fields(user)
        if self.errors:
            raise ValidationError(message='missing_fields', payload=self.errors)

    def submit(self, user, error_callback_url=None):
        raise NotImplemented('subclass a new submit function for %s' % self.__class__)


class OVRError(Exception):
    status_code = 400

    def __init__(self, form, message, status_code=None, payload=None, error_callback_url=None):
        Exception.__init__(self)
        self.form = form
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

        safety_first = self.to_dict()
        error = {
            "message": safety_first["message"],
            "payload": safety_first["payload"],
            "status": "failure",
            "code": self.status_code,
            "form_class": form.__class__.__name__
        }

        log_id = log_response(form, error)

        error["reference"] = log_id
        error["uid"] = str(form.get_uid())

        if error_callback_url:
            requests.post(error_callback_url, error)

    def to_dict(self):
        rv = {}
        try:
            json.dumps(self.payload)
            rv['payload'] = self.payload
        except:
            rv['payload'] = '(Could not be JSON-encoded)'
        rv['message'] = self.message
        return rv
