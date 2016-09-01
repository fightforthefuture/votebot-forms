from base_ovr_form import BaseOVRForm, OVRError
from form_utils import get_address_components, options_dict, split_date, clean_browser_response, ValidationError, log_form
import sys, traceback
import requests

class Georgia(BaseOVRForm):
    def __init__(self):
        super(Georgia, self).__init__('https://registertovote.sos.ga.gov/GAOLVR/welcometoga.do')
        # todo: you can check if you are registered at https://www.mvp.sos.ga.gov/MVP/mvp.do
        self.success_string = 'TBD'
        self.add_required_fields(['will_be_18', 'legal_resident', 'disenfranchised', 'incompetent'])

    def parse_errors(self):
        if self.errors:
            return self.errors

        messages = []
        for error in self.browser.select('.fontError'):
            if error.text.strip() != '':
                messages.append({'error': error.text})
        return messages

    def welcome(self, user, form):
        self.browser.submit_form(form, submit=form['ddsIdButton'])
        return form

    def minimum_requirements(self, user, form):
        form['citizenVer'].checked = user['us_citizen']
        form['ageVer'].checked = user['will_be_18']
        form['stateVer'].checked = user['legal_resident']
        form['felonyVer'].checked = not user['disenfranchised']
        form['mentally'].checked = not user['incompetent']

        # every GA form has a "back" button which also does a submit, so we have to specify
        self.browser.submit_form(form, submit=form['beginReg'])
        return form

    def personal_information(self, user, form):
        form = self.browser.get_form("formId")

        # update form action, this happens in javascript on validateForm
        form.action = 'reqConsentAndDecline.do'

        # new voter
        form['changeType'].value = 'NV'

        # county select from list
        form['county'].value = options_dict(form['county'])[user['county'].upper()]

        form['lastName'].value = user['last_name'].upper()
        form['firstName'].value = user['first_name'].upper()

        (year, month, day) = split_date(user['date_of_birth'])
        form['dobDate'].value = '/'.join([month, day, year])

        form['ddsId'].value = user['state_id_number']

        self.browser.submit_form(form, submit=form['next'])

        return form

    def consent_use_signature(self, user, form):
        if user.get('consent_use_signature'):
            form['consent'].value = '1'
        self.browser.submit_form(form, submit=form['next'])
        return form

    def residence_address(self, user, form):
        # reassemble address_components to match street name dropdowns
        # in the browser this autofills, but we get to do it manually
        address_components = get_address_components(user['address'], user['city'], user['state'], user['zip'])

        form['streetNum'].value = address_components['primary_number']

        full_street_name = address_components['street_name']
        if 'street_predirection' in address_components:
            full_street_name = address_components['street_predirection'] + ' ' + full_street_name

        if 'street_suffix' in address_components:
            full_street_name += ' %s' % address_components['street_suffix']

        form['streetName1'].value = options_dict(form['streetName1'])[full_street_name.upper()]

        street_value = form['streetName1'].value
        city_value = self.get_postal_city(street_value, address_components['county_name'])
        # add city option to dropdown
        form['city'].options.append(city_value)
        form['city'].value = city_value

        form['state'].value = address_components['state_abbreviation']
        form['zip5'].value = address_components['zipcode']

        self.browser.submit_form(form, submit=form['next'])
        return form

    def get_postal_city(self, street_value, county):
        # GA does clever stuff with modifying the select options in javascript
        # use the same request session from browser to maintain cookies
        r = self.browser.session.request("GET", "https://registertovote.sos.ga.gov/GAOLVR/getPostalCities.do",
                     params={'streetName': street_value, 'countyName': county.upper()})
        p = r.json()
        return p[0]['key']

    def general_information(self, user, form):
        # these fields are all optional, fill in only if defined
        if user.get('gender'):
            form['gender'] = user['gender'].capitalize()
        # poll_worker
        if user.get('ssn_last_4'):
            form['ssnId'] = user['ssn_last_4']
            # also accepts full SSN, but no dashes
        if user.get('email'):
            form['emailId'] = user['email']
        if user.get('phone'):
            form['telephone'] = user['phone']
            # format?
        # ethnicity requires a dropdown, and is optional
        # skip it
        self.browser.submit_form(form, submit=form['next'])
        return form

    def review_information(self, user, form):
        if user['us_citizen']:
            form['citizenCheck'].value = "on"
        else:
            self.add_error("You must be a U.S. Citizen.", field='us_citizen')

        if user['will_be_18']:
            form['ageCheck'].value = "on"
        else:
            self.add_error('You must be 18 by Election Day.', field='will_be_18')

        if not user.get('legal_resident'):
            self.add_error('You must be a legal resident of Georgia.', field='legal_resident')
        if user.get('disenfranchised'):
            self.add_error('You must not be serving a sentence for having been convicted of a felony involving moral turpitude.', field='disenfranchised')
        if user.get('incompetent'):
            self.add_error('You must not have been judicially declared to be mentally incompetent.', field='incompetent')

        user_is_eligible = user['legal_resident'] and (not user['disenfranchised']) and (not user['incompetent'])
        if user_is_eligible:
            form['checkbox'].value = "on"

        if self.errors:
            return False

        # ENABLE WHEN DEPLOY
        #self.browser.submit_form(form, submit=form['submitBtn'])

    def submit(self, user, error_callback_url=None):
        self.error_callback_url = error_callback_url

        try:
            # format is: [kwargs to select / identify form, method to call with form]
            # frustratingly, GA uses the same methods and IDs for each form
            # and inconsistent GAOLVR prefixing...
            forms = [
                [{'action': "beginRegistration.do"}, self.welcome],
                [{'action': "registrationRequestToStep1.do"}, self.minimum_requirements],
                [{'id': 'formId'}, self.personal_information],
                [{'action': "regStep3.do"}, self.consent_use_signature],
                [{'action': "/GAOLVR/regStep3.do"}, self.residence_address],
                [{'action': "/GAOLVR/regStep4.do"}, self.general_information],
                [{'action': "/GAOLVR/summary.do"}, self.review_information],
            ]

            for form_kwargs, handler in forms:

                step_form = self.browser.get_form(**form_kwargs)

                if step_form:
                    print "running handler", handler.__name__
                    handler(user, step_form)

                errors = self.parse_errors()
                if errors:
                    print "errors", errors
                    return {'status': 'failure', 'step': handler.__name__, 'errors': errors}

                if not step_form:
                    print "no form", form_kwargs
                    return {'status': 'failure', 'step': handler.__name__, 'error': 'no form %s' % form_kwargs}

            success_page = clean_browser_response(self.browser)
            if self.success_string in success_page:
                return {'status': 'success'}
            else:
                return {'status': 'failure'}

        except ValidationError, e:
            raise OVRError(self, message=e.message, payload=e.payload, error_callback_url=self.error_callback_url)

        except Exception, e:
            ex_type, ex, tb = sys.exc_info()
            print ex_type, ex
            print traceback.format_tb(tb)
            raise OVRError(self, message="%s %s" % (ex_type, ex), payload=traceback.format_tb(tb), error_callback_url=self.error_callback_url)
