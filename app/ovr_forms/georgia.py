from base_ovr_form import BaseOVRForm, OVRError
from form_utils import split_date, ValidationError
import sys, traceback

class Georgia(BaseOVRForm):
    def __init__(self):
        super(Georgia, self).__init__('https://registertovote.sos.ga.gov/GAOLVR/welcometoga.do')
        # todo: you can check if you are registered at https://www.mvp.sos.ga.gov/MVP/mvp.do
        self.add_required_fields(['will_be_18', 'legal_resident', 'disenfranchised', 'mentally_competent'])

    def welcome(self):
        ovr_welcome_form = self.browser.get_form()
        # select OVR
        self.browser.submit_form(ovr_welcome_form, submit=ovr_welcome_form['ddsIdButton'])
        return ovr_welcome_form

    def minimum_requirements(self, user):
        min_req_form = self.browser.get_form()

        # todo: these will need to be boolean for the form.
        # we'll need to normalize truthy values from SMS/etc. input
        min_req_form['citizenVer'].checked = user['us_citizen']
        min_req_form['ageVer'].checked = user['will_be_18']
        min_req_form['stateVer'].checked = user['legal_resident']
        min_req_form['felonyVer'].checked = not user['disenfranchised']
        min_req_form['mentally'].checked = user['mentally_competent']
        
        # every GA form has a "back" button which also does a submit, so we have to specify
        self.browser.submit_form(min_req_form, submit=min_req_form['beginReg'])
        return min_req_form

    def get_county(self, user):
        # this takes place in a modal on the site.
        county_req = self.browser.session.get('https://registertovote.sos.ga.gov/GAOLVR/getCounties.do?zipcode=%s' % user['zip'])
        county_json = county_req.json()
        return county_json[0]['key']

    def registration(self, user):
        registration_form = self.browser.get_form()
        # new voter
        registration_form['changeType'].value = 'NV'
        registration_form['county'].value = self.get_county(user)
        
        registration_form['lastName'].value = user['last_name']
        registration_form['firstName'].value = user['first_name']

        (year, month, day) = split_date(user['date_of_birth'])
        registration_form['dobDate'].value = '/'.join([month, day, year])

        registration_form['ddsId'].value = user['state_id_number']
        
        self.browser.submit_form(registration_form, submit=registration_form['next'])
        return registration_form

    def submit(self, user, error_callback_url = None):

        self.error_callback_url = error_callback_url

        try:
            self.welcome()
            self.minimum_requirements(user)
            self.registration(user)
            # todo: I need a valid GA driver's license.
        except ValidationError, e:
            raise OVRError(self, message=e.message, payload=e.payload, error_callback_url=self.error_callback_url)

        except Exception, e:
            ex_type, ex, tb = sys.exc_info()
            raise OVRError(self, message="%s %s" % (ex_type, ex), payload=traceback.format_tb(tb), error_callback_url=self.error_callback_url)