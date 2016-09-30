from base_ovr_form import BaseOVRForm, OVRError
from form_utils import (ValidationError, clean_browser_response,
                        split_date, split_name, parse_gender, bool_to_int,
                        get_party_from_list, get_ethnicity_from_list, coerce_string_to_list)
from form_address import get_address_from_freeform, get_street_address_from_components, get_address_unit_from_components
import sys, traceback, os

PA_API_KEY = os.environ.get('PA_API_KEY', '503296D9-C780-4A15-8803-1C829544258C')  # default to their testing key
PA_API_URL = 'https://paovrwebapi.votespa.com/SureOVRWebAPI/api/ovr?JSONv2&sysparm_AuthKey=%s&sysparm_Language=0' % PA_API_KEY


class Pennsylvania(BaseOVRForm):

    def __init__(self):
        super(Pennsylvania, self).__init__(PA_API_URL + '&sysparm_action=GETXMLTEMPLATE')
        self.add_required_fields(['will_be_18', 'legal_resident', 'county', 'state_id_number', 'declaration'])
        self.success_string = 'TBD'

    def parse_errors(self):
        if self.errors:
            return self.errors

    def submit(self, user, error_callback_url=None):
        self.set_user_agent(user)
        self.error_callback_url = error_callback_url

        try:
            self.xml_api(user)
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

    def xml_api(self, user):
        # PA has a direct XML API
        # field definitions from http://www.dos.pa.gov/VotingElections/OtherServicesEvents/Documents/PAOVRWebAPIFieldDefinition%20Modified%209-8-2016.xlsx

        # interactive submission
        form = {'batch': 1}

        # your name
        form['FirstName'] = user['first_name'][:30]
        form['LastName'] = user['last_name'][:30]
        form['MiddleName'] = user.get('middle_name', '')  # not required, but send if we have it

        # eligibility
        form['united-states-citizen'] = bool_to_int(user.get('us_citizen'))
        form['eighteen-on-election-day'] = bool_to_int(user.get('us_citizen'))

        # reason
        if 'has_previous_name' in user:
            form['name-update'] = 1
        elif 'has_previous_address' in user:
            form['address-update'] = 1
        elif '':
            form['ispartychange'] = 1
        else:
            form['isnewregistration'] = 1

        # about you
        (year, month, day) = split_date(user['date_of_birth'])
        form['DateOfBirth'] = '/'.join([month, day, year])
        if 'gender' in user:
            try:
                gender = parse_gender(user.get('gender'))
            except ValidationError:
                gender = 'U'  # for unknown, cool PA
            form['Gender'] = gender
        if 'ethnicity' in user:
            ethnicity = get_ethnicity_from_list(user.get('ethnicity'))
            pa_race_values = {'asian-pacific': 'A', 'native-american': 'I', 'black': 'B', 'hispanic': 'H', 'other': 'O', 'white': 'W'}
            form['Race'] = pa_race_values.get(ethnicity, '')

        if 'phone' in user:
            phone = user.get('phone').replace('+1', '')
            form['Phone'] = '-'.join(phone[0:3], phone[3:6], phone[6:10])
        if 'email' in user:
            form['Email'] = user.get('email')

        # your address
        form['streetaddress'] = user.get('address')[:40]
        form['unitnumber'] = user.get('address_unit', '')
        form['city'] = user.get('city')[:35]
        form['zipcode'] = user.get('zipcode')
        form['county'] = user.get('county')[:20]
        # municipality?

        # address where you receive mail
        if 'has_separate_mailing_address' in user:
            # parse mailing address components
            mailing_components = get_address_from_freeform(user['separate_mailing_address'])['components']

            # reassemble from normalized
            mailing_address = "%s %s".strip() % (get_street_address_from_components(mailing_components),
                                         get_address_unit_from_components(mailing_components))
            form['Mailingaddress'] = mailing_address
            form['mailingcity'] = mailing_components['city_name']
            form['mailingstate'] = mailing_components['state_abbreviation']
            form['mailingzipcode'] = mailing_components['zipcode']

        # identification
        if 'state_id_number' in user:
            form['drivers-license'] = user.get('state_id_number')
        elif ('ssn_last4' in user) and ('signature_image' in user):
            # if no DL, signature image and SSN[:-4] are required
            form['ssn4'] = user.get('ssn_last4')
            image_contents = self.browser.session.get(user['signature_image'])  # get contents from URL
            form['signatureimage'] = image_contents.content.encode('base64')
            form['continueAppSubmit'] = 1
        else:
            raise ValidationError(message='A valid PA ID or SSN and signature image is required', payload='state_id_number')

        # political party
        party = get_party_from_list(user.get('political_party'), ['Democratic', 'Republican', 'Other', 'None'])
        if party:
            pa_race_values = {'Democratic': 'D', 'Republican': 'R', 'Other': 'O', 'None': 'NF'}
            form['politicalparty'] = pa_race_values.get(party, 'NF')
            if form['politicalparty'] == 'O':
                form['otherpoliticalparty'] = user.get('political_party')[:50]  # send PA whatever the person entered

        # voting assistance
        if user.get('needs_voting_assistance'):
            form['needhelptovote'] = 1
            pa_assistance_values = {
                'deaf or hard of hearing': 'HI',
                'blind or have difficulty seeing': 'VSI',
                'wheelchair': 'WC',
                'physical disability': 'PD',
                'need help reading': 'IL',
                'do not speak English well': 'LN'
            }
            assistance_type = coerce_string_to_list(user['needs_voting_assistance'], pa_assistance_values.keys())
            form['typeofassistance'] = pa_assistance_values.get(assistance_type, '')
            if form['typeofassistance'] == 'LN':
                form['preferredlanguage'] = user.get('language')

        # voting information that has changed
        form['voterregnumber'] = user.get('previous_registration_number', '')
        form['previousregyear'] = user.get('previous_registration_year', '')

        if 'has_previous_name' in user:
            prev_first, prev_middle, prev_last = split_name(user.get('previous_name'))
            form['previousregfirstname'] = prev_first
            form['previousregmiddlename'] = prev_middle
            form['previousreglastname'] = prev_last

        if 'has_previous_address' in user:
            form['previousregaddress'] = user['previous_address']
            form['previousregcity'] = user['previous_city']
            form['previousregstate'] = user['previous_state']
            form['previousregzip'] = user['previous_zip']
            form['']

        # declaration
        if user['declaration'] is True:
            form['declaration1'] = 1
        else:
            raise ValidationError(message='you must agree to the PA Declaration', payload=user.get('declaration'))

        # optional...
        # help with the form
        # be a poll worker
        # second email

        # submit!
        r = self.browser.session.post(PA_API_URL + '&sysparm_action=SETAPPLICATION', params=form)
        if r.status_code == 200:
            # TODO get transaction ID
            return True
        else:
            raise ValidationError(message='unable to post to PA API', payload=r.content)

