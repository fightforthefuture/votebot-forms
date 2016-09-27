from base_ovr_form import BaseOVRForm, OVRError
from form_utils import (ValidationError, clean_browser_response,
                        options_dict, split_date, split_name, parse_gender)
from form_address import (get_address_components, get_street_name_from_components)
import robobrowser
import sys, traceback


class Georgia(BaseOVRForm):
    def __init__(self):
        super(Georgia, self).__init__('https://registertovote.sos.ga.gov/GAOLVR/welcometoga.do')
        self.success_string = 'You are NOT officially registered to vote until this application is approved.'
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
        if user['us_citizen']:
            form['citizenVer'].checked = True
            form['citizenVer'].value = "on"

        if user['will_be_18']:
            form['ageVer'].checked = True
            form['ageVer'].value = "on"

        if user['legal_resident']:
            form['stateVer'].checked = True
            form['stateVer'].value = "on"

        if not user['disenfranchised']:
            form['felonyVer'].checked = True
            form['felonyVer'].value = "on"

        if not user['incompetent']:
            form['mentally'].checked = True
            form['mentally'].value = "on"

        # every GA form has a "back" button which also does a submit, so we have to specify
        self.browser.submit_form(form, submit=form['beginReg'])
        return form

    def personal_information(self, user, form):
        form = self.browser.get_form("formId")

        # update form action, this happens in javascript on validateForm
        form.action = 'reqConsentAndDecline.do'

        if user('has_previous_address'):
            # change voter registration
            form['changeType'].value = 'CV'
            form['_addrChange'].checked = 'checked'
            # don't actually change registration here, do it later in general information
        else:
            # new voter registration
            form['changeType'].value = 'NV'

        if user.get('has_previous_name'):
            form['changeType'].value = 'CV'
            form['_nmChange'].checked = 'checked'
            (prev_first, prev_middle, prev_last) = split_name(user.get('previous_name'))
            form['preFirstName'].value = prev_first
            form['preLastName'].value = prev_last

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
            form['consent'].value = '0'  # incredibly, this means "yes", 1 means "no"
        self.browser.submit_form(form, submit=form['next'])
        return form

    def residence_address(self, user, form):
        # reassemble address_components to match street name dropdowns
        # in the browser this autofills, but we get to do it manually
        address_components = get_address_components(user['address'], user['city'], user['state'], user['zip'])

        form['streetNum'].value = address_components['primary_number']

        full_street_name = get_street_name_from_components(address_components)
        form['streetName1'].value = options_dict(form['streetName1'])[full_street_name.upper()]

        street_value = form['streetName1'].value

        # look up postal city key and rural_flag from street_value
        postal_city = self.get_postal_city(street_value, address_components['county_name'])[0]
        rural_flag = postal_city['fl_Rural_Flag']
        form['ruralcityFlag'].value = rural_flag.lower()
        if rural_flag == "Y":
            form['rural_city'].options = (postal_city['key'], )
            form['rural_city'].value = str(postal_city['key'])
        else:
            # replace weird city selector with a regular input
            form.fields.pop('city')
            city_field = robobrowser.forms.fields.Input('<input type="hidden" id="city" name="city"></input>')
            city_field.value = str(postal_city['key'])
            form.add_field(city_field)

        # of course, there's also a hidden cityName field to append
        city_name = robobrowser.forms.fields.Input('<input type="hidden" id="cityName" name="cityName"></input>')
        city_name.value = address_components['city_name'].upper()
        form.add_field(city_name)

        form['state'].value = address_components['state_abbreviation']
        form['zip5'].value = address_components['zipcode']
        form['countyS3'].value = address_components['county_name'].upper()

        # update form action, this happens in javascript on validateForm
        form.action = 'regStep4.do'

        self.browser.submit_form(form, submit=form['next'])
        return form

    def get_postal_city(self, street_value, county):
        # GA does clever stuff with modifying the select options in javascript
        # try to mimic it
        r = self.browser.session.get("https://registertovote.sos.ga.gov/GAOLVR/getPostalCities.do",
                     params={'streetName': street_value, 'countyName': county.upper()})
        return r.json()

    def general_information(self, user, form):
        # these fields are all optional, fill in only if defined
        if user.get('gender'):
            form['gender'].options = ['Male', 'Female']  # they have two buttons with the same name but different ids
            gender_str = parse_gender(user['gender'])  # coerces free text to M/F
            if gender_str is 'F':
                form['gender'].value = 'Female'
            elif gender_str is 'M':
                form['gender'].value = 'Male'
            else:
                raise ValidationError(message='parse_gender error', payload=user['gender'])

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

        # previous address appears here
        if user.get('has_previous_address'):
            prev_address_components = get_address_components(user['previous_address'], user['previous_city'], user['previous_state'], user['previous_zip'])
            form['preStreetNo'].value = prev_address_components['primary_number']
            form['preStreetName'].value = get_street_name_from_components(prev_address_components).upper()
            if 'secondary_number' in prev_address_components:
                form['preAptNo'].value = prev_address_components['secondary_number']
            form['prePostalCity'].value = prev_address_components['city_name']
            form['ctl00$MainContent$TxtPrevRegZip'].value = prev_address_components['zipcode']
            form['preState'].value = prev_address_components['state_abbreviation']

        form.action = 'summary.do'
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
            form['checkbox'].checked = "checked"
            form['checkbox'].value = "on"

        if self.errors:
            return False

        # mimic their javascript as closely as possible
        hidden_clicker = robobrowser.forms.fields.Input('<input type="hidden" id="confirmSubmit_Clicker" name="confirmSubmit_Clicker"></input>')
        form.add_field(hidden_clicker)
        form.action = 'success.do'

        self.browser.submit_form(form, submit=form['submitBtn'])

    def confirmation_email(self, user, form):
        # send user email confirmation with reference number
        if user.get('email'):
            r = self.browser.session.get('https://registertovote.sos.ga.gov/GAOLVR/sendMail.do',
                params={'emailId': user['email'], 'referenceNumber': form['referenceNumber'].value})

    def submit(self, user, error_callback_url=None):
        self.set_user_agent(user)
        self.error_callback_url = error_callback_url

        try:
            # format is: [kwargs to select / identify form, method to call with form]
            forms = [
                [{}, self.welcome],
                [{}, self.minimum_requirements],
                [{}, self.personal_information],
                [{}, self.consent_use_signature],
                [{'id': 'formId'}, self.residence_address],  # there are two forms on this page, but one is blank
                [{}, self.general_information],
                [{}, self.review_information],
                [{}, self.confirmation_email],
            ]

            for form_kwargs, handler in forms:

                step_form = self.browser.get_form(**form_kwargs)

                if step_form:
                    handler(user, step_form)

                errors = self.parse_errors()
                if errors:
                    raise ValidationError(message='field_errors', payload=errors)

                if not step_form:
                    raise ValidationError(message='no_form_found', payload=handler.__name__)

            success_page = clean_browser_response(self.browser)
            if self.success_string in success_page:
                return {'status': 'success'}
            else:
                raise ValidationError(message='no_success_string')

        except ValidationError, e:
            raise OVRError(self, message=e.message, payload=e.payload, error_callback_url=self.error_callback_url)

        except Exception, e:
            ex_type, ex, tb = sys.exc_info()
            print ex_type, ex
            print traceback.format_tb(tb)
            raise OVRError(self, message="%s %s" % (ex_type, ex), payload=traceback.format_tb(tb), error_callback_url=self.error_callback_url)
