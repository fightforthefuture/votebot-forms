from robobrowser import RoboBrowser
import json

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
    def __init__(self, start_url):
        self.browser = RoboBrowser(parser='html.parser', user_agent='HelloVote.org', history=True)
        self.browser.open(start_url)
        self.required_fields = BASE_REQUIRED_FIELDS
        self.errors = []

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

    def validate(self, user):
        self.check_required_fields(user)
        if self.errors:
            raise ValidationError(message='missing_fields', payload=self.errors)

    def submit(self, user):
        raise NotImplemented('subclass a new submit function for %s' % self.__class__)


class ValidationError(Exception):
    status_code = 400

    def __init__(self, message, payload=None):
        self.message = message
        self.payload = payload


class OVRError(Exception):
    status_code = 400

    def __init__(self, form, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.form = form
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload


    def to_dict(self):
        rv = {}
        try:
            json.dumps(self.payload)
            rv['payload'] = self.payload    
        except:
            rv['payload'] = '(Could not be JSON-encoded)'        
        rv['message'] = self.message
        return rv
