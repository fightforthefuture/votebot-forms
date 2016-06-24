from robobrowser import RoboBrowser

BASE_REQUIRED_FIELDS = [
    'first_name',
    'last_name',
    'state',
    'date_of_birth',
    'home_address',
    'home_city',
    'home_zip',
    'us_citizen',
    'not_a_felon',
    'id_number'
]


class BaseOVRForm(object):
    def __init__(self, start_url):
        self.browser = RoboBrowser(parser='html.parser', user_agent='votebot-forms FightForTheFuture', history=True)
        self.browser.open(start_url)
        self.required_fields = BASE_REQUIRED_FIELDS

    def check_required_fields(self, user):
        for field in self.required_fields:
            if field not in user:
                raise OVRError('%s is required' % field)

    def validate(self, user):
        self.check_required_fields(user)

    def submit(self, user):
        print "submitting user data", user


class OVRError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv
