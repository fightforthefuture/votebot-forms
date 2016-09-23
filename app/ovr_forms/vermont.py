from base_ovr_form import BaseOVRForm, OVRError
from form_utils import ValidationError, clean_browser_response, options_dict, split_date, split_name, get_address_components
import sys, traceback


class Vermont(BaseOVRForm):

    def __init__(self):
        super(Vermont, self).__init__('https://olvr.sec.state.vt.us/')
        self.add_required_fields(['will_be_18', 'legal_resident', 'state_id_number', 'voters_oath'])
        self.success_string = 'Thank you for completing your voter registration application'

    def parse_errors(self):
        if self.errors:
            return self.errors

        messages = []
        for error in self.browser.select('.errorsPlaceHolder1 li'):
            messages.append({'error': error.text})
        for error in self.browser.select('.text-danger'):
            messages.append({'error': error.text})
        return messages

    def submit(self, user, error_callback_url=None):
        self.set_user_agent(user)
        self.error_callback_url = error_callback_url

        try:
            # this one's a little different, all form stepping is in javascript
            # persist same form between handlers, don't submit until end
            self.set_registration_type(user)
            form = self.browser.get_form()

            handlers = [
                self.eligibility,
                self.voter_information,
                self.address,
                self.previous_info,
                self.review_affirm,
                self.email_receipt
            ]

            for handler in handlers:
                handler(user, form)
                errors = self.parse_errors()
                if errors:
                    raise ValidationError(message='field_errors', payload=errors)

            success_page = clean_browser_response(self.browser)
            if self.success_string in success_page:
                return {'status': 'success'}
            else:
                raise ValidationError(message='no_success_string')

        except ValidationError, e:
            raise OVRError(self, message=e.message, payload=e.payload, error_callback_url=self.error_callback_url)

        except Exception, e:
            ex_type, ex, tb = sys.exc_info()
            raise OVRError(self, message="%s %s" % (ex_type, ex), payload=traceback.format_tb(tb), error_callback_url=self.error_callback_url)

    def set_registration_type(self, user):
        token = self.browser.find("input", {"name": "__RequestVerificationToken"})['value']
        request_data = {'HaveDL': True if 'state_id_number' in user else False,
             'Source': ''}
        r = self.browser.session.post('https://olvr.sec.state.vt.us/Registration/SavetheRequest',
            request_data, headers={'__RequestVerificationToken': token,
                                   'X-Requested-With': 'XMLHttpRequest'})
        if (r.status_code >= 400):
            raise ValidationError(message='unable to get token')
        self.browser.open('https://olvr.sec.state.vt.us/Registration/RegistrationDetails',
                           headers={'__RequestVerificationToken': token})

    def eligibility(self, user, form):
        if user['us_citizen']:
            form['chkCitizen'].checked = 'checked'
        if user['will_be_18']:
            form['chkAgeValid'].checked = 'checked'
        if user['legal_resident']:
            form['chkVTResident'].checked = 'checked'

    def voter_information(self, user, form):
        form['townId'].value = options_dict(form['townId'])[user['city'].upper()]

        form['firstName'].value = user['first_name']
        form['lastName'].value = user['last_name']

        (year, month, day) = split_date(user['date_of_birth'])
        form['Dob'].value = '/'.join([month, day, year])

        form['DLNumber'].value = user['state_id_number']
        form['email'].value = user['email']

    def address(self, user, form):
        address_components = get_address_components(user['address'], user['city'], user['state'], user['zip'])

        form['addressNumber'].value = address_components['primary_number']
        street_name = address_components['street_name']
        if 'street_predirection' in address_components:
            street_name = "%s %s" % (address_components['street_predirection'], street_name)
        if 'street_postdirection' in address_components:
            street_name = "%s %s" % (street_name, address_components['street_postdirection'])
        form['addressStreet1'].value = street_name

        if user.get('address_unit') and not user.get('address_unit').lower() == "none":
            form['addressUnit'].value = user.get('address_unit')

        form['addressCity'].value = user['city']
        form['addressZip'].value = user['zip']

        if user.get('has_separate_mailing_address'):
            # TODO
            pass
        else:
            form['chkSameResidence'].checked = 'checked'

    def previous_info(self, user, form):

        if user.get('has_previous_name'):
            prev_first, prev_middle, prev_last = split_name(user.get('previous_name'))
            form['previousFirstName'] = prev_first
            form['previousMiddleName'] = prev_middle
            form['previousLastName'] = prev_last

        if user.get('has_previous_address'):
            form['chkPrvVote'].value = 'Y'
            form['chkPrvVote'].checked = 'checked'

            address_components = get_address_components(user['previous_address'], user['previous_city'], user['previous_state'], user['previous_zip'])
            street_name = address_components['street_name']
            if 'street_predirection' in address_components:
                street_name = "%s %s" % (address_components['street_predirection'], street_name)
            if 'street_postdirection' in address_components:
                street_name = "%s %s" % (street_name, address_components['street_postdirection'])
            form['previousAddressLine1'].value = street_name

            form['previousAddressCity'].value = address_components['city_name']
            form['previousAddressState'].value = address_components['state_abbreviation']
            form['previousAddressZip'].value = address_components['zipcode']

        else:
            form['chkPrvVote'].value = 'N'
            form['chkPrvVote'].checked = 'checked'

    def review_affirm(self, user, form):

        if user.get('first_time_registering'):
            # "If you are registering to vote in Vermont for the first time, you must include a photocopy of an acceptable form of ID."
            # however, this requirement is waived if you are registering as part of a voter registration drive
            # per https://www.sec.state.vt.us/elections/voters/registration.aspx#VoterRegDrive

            # TODO, investigate getting photo of ID over MMS
            pass

        if user['legal_resident']:
            form['chkResidentConfirm'].checked = 'checked'

        if user.get('voters_oath'):
            form['chkVoterAuth'].checked = 'checked'

        self.browser.submit_form(form, submit=form['btnContinue'])

    def email_receipt(self, user, form):
        email_form = self.browser.get_form({'id': 'frmEmailSend'})
        if email_form:
            email_form['txtEmail'].value = user.get('email')
            self.browser.submit_form(email_form)
