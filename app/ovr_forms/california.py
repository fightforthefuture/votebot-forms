from base_ovr_form import BaseOVRForm, OVRError
from form_utils import (ValidationError, clean_browser_response,
                        bool_to_string, split_date, split_name, options_dict, get_party_from_list)
from form_address import (get_address_from_freeform, get_street_address_from_components, get_address_unit_from_components)
from robobrowser.forms.fields import Input
import sys, traceback


class California(BaseOVRForm):
    def __init__(self):
        super(California, self).__init__('https://covr.sos.ca.gov/?language=en-US')
        self.add_required_fields(['will_be_18', 'political_party', 'disenfranchised',
                                 'ssn_last4', 'county', 'consent_use_signature'])
        self.success_string = "Your voter registration application is now complete."

    def submit(self, user, error_callback_url=None):
        self.set_user_agent(user)
        self.error_callback_url = error_callback_url

        try:
            forms = [
                self.step1,
                self.step2,
                self.step3,
                self.step4,
                self.step5
            ]

            for handler in forms:
                step_form = self.browser.get_form()
                if step_form:
                    handler(step_form, user)

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
            raise OVRError(self, message="%s %s" % (ex_type, ex), payload=traceback.format_tb(tb), error_callback_url=self.error_callback_url)

    def parse_errors(self):
        errors_dict = {}
        for error in self.browser.find_all(class_='field-validation-error'):
            errors_dict[error['data-valmsg-for']] = error.text
        return errors_dict

    def submit_form_field(self, form, name):
        submit_button = form[name]
        submit_value = submit_button.value

        # weird workaround required to add a hidden copy of the same value
        # required so that the state sends us a 302 redirect, instead of a 404
        form.add_field(Input("<input type='hidden' name='%s' value='%s' />" % (name, submit_value)))
        self.browser.submit_form(form, submit=submit_button)

    def step1(self, form, user):
        if user['us_citizen'] and (user['state'].upper() == 'CA'):
            form['ClassificationType'].value = '1'  # default check 'A U.S. citizen residing in California.'
        else:
            raise ValidationError(message='must be US citizen residing in California to register', payload={
                'us_citizen': user['us_citizen'],
                'state': user['state']
            })
        self.submit_form_field(form, 'GoToNext')

        #  TODO, do we have to check against others voter types?
        #  A U.S. citizen residing in California.
        #  A member of the Uniformed Services or Merchant Marine on active duty outside my county.
        #  An eligible spouse or dependent of a member of the Uniformed Services or Merchant Marine on active duty outside my county.
        #  An activated National Guard member on State orders outside my county.
        #  A U.S. citizen residing outside the U.S. temporarily.
        #  A U.S. citizen residing outside the U.S. indefinitely.
        #  A U.S. citizen and have never resided in the U.S.

    def step2(self, form, user):
        #  Eligibility
        form['IsUSCitizen'].value = bool_to_string(user['us_citizen'])
        if user['will_be_18']:
            form['RegistrationChoice'].value = '1'
            # I will be 18 or older by the next election.
        else:
            # other options:
            # form['RegistrationChoice'].value = '2'
            # I am a 16 or 17 years old and I would like to pre-register to vote.
            # don't handle this yet, needs update in votebot-api
            raise ValidationError(message='no county match', payload={
                'will_be_18': user['will_be_18'],
                'date_of_birth': user['date_of_birth']
            }) 

        prefix_options = options_dict(form['Prefix'])
        if 'name_prefix' in user:
            form['Prefix'].value = prefix_options.get(user['name_prefix'])
        form['FirstName'].value = user['first_name']
        form['MiddleName'].value = user.get('middle_name')
        form['LastName'].value = user['last_name']
        suffix_options = options_dict(form['Suffix'])
        if 'name_suffix' in user:
            form['Suffix'].value = suffix_options.get(user['name_suffix'])

        form['EmailAddress'].value = user.get('email', '')
        form['ConfirmEmail'].value = user.get('email', '')
        if user.get('phone'):
            phone = user.get('phone').replace('+1', '').replace('-', '')
            form['PhoneNumber'].value = phone

        # change of name
        if user.get('has_previous_name'):
            form['IsPreviouslyRegistered'].checked = 'checked'
            (prev_first, prev_middle, prev_last) = split_name(user.get('previous_name', ''))
            form['Previous.FirstName'] = prev_first
            form['Previous.MiddleName'] = prev_middle
            form['Previous.LastName'] = prev_last

        # change of address
        if user.get('has_previous_adress'):
            form['IsPreviouslyRegistered'].checked = 'checked'
            form['Previous.StreetAddress'] = user.get('previous_address', '')
            form['Previous.ApartmentLotNumber'] = user.get('previous_address_unit', '')
            form['Previous.City'] = user.get('previous_city', '')
            form['Previous.Zip'] = user.get('previous_zip', '')
            form['Previous.StateId'] = user.get('previous_state', '')

        # separate mailing address
        if user.get('has_separate_mailing_addresss'):
            form['IsDifferentMailingAddress'].checked = 'checked'

            mailing_components = get_address_from_freeform(user.get('separate_mailing_address'))
            form['Mailing.StreetAddress'] = get_street_address_from_components(mailing_components)
            form['Mailing.ApartmentLotNumber'] = get_address_unit_from_components(mailing_components)
            form['Mailing.City'] = mailing_components('city_name')
            form['Mailing.State'] = mailing_components('state_abbreviation')
            form['Mailing.Zip'] = mailing_components('zipcode')

        (year, month, day) = split_date(user['date_of_birth'], padding=False)
        form['MonthOfBirth'].value = month
        form['DayOfBirth'].value = day
        form['YearOfBirth'].value = year

        #  ID and last 4 of SSN (CA requires both!)
        if 'state_id_number' in user:
            form['CaliforniaID'].value = user.get('state_id_number')
        else:
            form['HasNoCaliforniaID'].value = bool_to_string(True)
            # we actually require this, so shouldn't get here, but just in case
        if user.get('ssn_last4') == "NONE":
            form['HasNoSSN'].value = bool_to_string(True)
        else:
            form['SSN4'].value = user.get('ssn_last4')

        #  Home and Mailing Address
        form['Home.StreetAddress'].value = user['address']
        form['Home.ApartmentLotNumber'].value = user.get('address_unit')
        form['Home.City'].value = user['city']
        form['Home.Zip'].value = user['zip']
        county_options = options_dict(form['Home.CountyId'])
        try:
            form['Home.CountyId'].value = county_options.get(user['county'].strip().upper())
        except KeyError:
            raise ValidationError(message='no county match', payload=user['county'])

        # Ethnicity (optional)
        if 'ethnicity' in user:
            ethnicity_options = options_dict(form['EthnicityId'])
            form['EthnicityId'].value = ethnicity_options.get(user['ethnicity'].upper(), ethnicity_options['OTHER'])

        #  Political Party Preference
        user["political_party"] = user["political_party"].strip().upper()

        # they have two inputs with the same name but separated by other elements
        # so robobrowser's _group_flat_tags creates two entries, which their server won't validate
        form.fields.pop('PoliticalPreferenceType')
        # recreate with just one
        PoliticalPreferenceType = Input("<input type='radio' name='PoliticalPreferenceType'/>")
        PoliticalPreferenceType.options = ['1', '2']
        form.add_field(PoliticalPreferenceType)

        if user['political_party'].lower() == 'independent' or user['political_party'].lower() == "none":
            PoliticalPreferenceType.value = '2'
            PoliticalPreferenceType.checked = 'checked'
            # also delete the politcal party select
            form.fields.pop('PoliticalPartyId')
        else:
            # mess with the DOM to un-disable Political Party
            del self.browser.select('select[name="PoliticalPartyId"]')[0]['disabled']

            PoliticalPreferenceType.value = '1'
            PoliticalPreferenceType.checked = 'checked'
            party_options = options_dict(form['PoliticalPartyId'])
            # do fuzzy match to political party options
            party_choice = get_party_from_list(user['political_party'], party_options.keys())

            if party_choice in party_options.keys():
                form['PoliticalPartyId'].value = party_options[party_choice]
            else:
                form['PoliticalPartyId'].value = party_options.get('Other')
                form['OtherPoliticalParty'].value = user['political_party']

        self.submit_form_field(form, 'GoToNext')

    def step3(self, form, user):
        #  Vote by Mail
        vote_by_mail_choice = bool_to_string(user.get('vote_by_mail', False), capitalize=True)
        # I want to get my ballot by mail before each election.
        form['IsPermanentVBM'].value = vote_by_mail_choice
        # I want to get my state voter information guide by mail before each statewide election.
        form['IsVIG'].value = vote_by_mail_choice
        # I want to get my sample ballot by mail before each election.
        form['IsSampleBallot'].value = vote_by_mail_choice

        #  Consent to Use Signature
        if user.get('consent_use_signature'):
            form['ConsentToUseSignature'].value = "True"
        else:
            raise ValidationError(message='consent_use_signature must be True', payload=user['consent_use_signature'])

        #  Affirmation
        user_is_eligible = user['us_citizen'] and user['will_be_18'] and (not user['disenfranchised'])
        
        # also add "information is true and correct"?
        form['Affirmation'].value = bool_to_string(user_is_eligible)
        form['Affirmation'].checked = 'checked'

        # not capitalized the same as other fields
        form['CanBePollWorker'].value = 'false'
        form['CanProvidePollingPlace'].value = 'false'
        
        self.submit_form_field(form, 'GoToNext')

    def step4(self, form, user):
        self.submit_form_field(form, 'GoToNext')

    def step5(self, form, user):
        form = self.browser.get_form(action='/en/OnlineVoterRegistration/PostForm')
        # Send an email receipt from the state
        if user.get('email'):
            form['Email'] = user['email']
            self.browser.submit_form(form)
