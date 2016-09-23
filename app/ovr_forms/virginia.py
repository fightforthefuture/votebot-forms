from base_ovr_form import BaseOVRForm, OVRError
from form_utils import options_dict, split_date, clean_browser_response, parse_gender, ValidationError
import sys, traceback
from robobrowser import RoboBrowser


class Virginia(BaseOVRForm):

    def __init__(self):
        super(Virginia, self).__init__('https://vote.elections.virginia.gov/Registration/Eligibility')
        self.add_required_fields(['county', 'legal_resident', 'incompetent', 'disenfranchised', 'ssn', 'gender',
                                 'privacy_notice', 'consent_use_signature', 'confirm_name_address', 'authorize_cancellation'])
        self.success_string = 'Your voter registration application has been submitted.'

    def parse_errors(self):
        if self.errors:
            return self.errors

        messages = []
        for error in self.browser.select('.field-validation-error'):
            if error.text.strip() != '':
                messages.append({'error': error.text})
        return messages

    def submit(self, user, error_callback_url=None):
        self.set_user_agent(user)
        self.error_callback_url = error_callback_url

        try:
            # format is: [kwargs to select / identify form, method to call with form]
            forms = [
                [{}, self.voting_eligibility],
                [{}, self.voting_identity],
                [{}, self.protected_voter],
                [{}, self.overseas_classification],
                [{}, self.absentee_ballot],
                [{}, self.residence_address],
                [{}, self.contact_information],
                [{}, self.affirmation]
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
                return {'status': 'failure'}

        except ValidationError, e:
            raise OVRError(self, message=e.message, payload=e.payload, error_callback_url=self.error_callback_url)

        except Exception, e:
            ex_type, ex, tb = sys.exc_info()
            print ex_type, ex
            print traceback.format_tb(tb)
            raise OVRError(self, message="%s %s" % (ex_type, ex), payload=traceback.format_tb(tb), error_callback_url=self.error_callback_url)

    def voting_eligibility(self, user, form):
        if user.get('us_citizen'):
            form['Eligibility.IsCitizen'] = "True"
        else:
            self.add_error("You must be a U.S. Citizen.", field='us_citizen')

        if user.get('legal_resident'):
            form['Eligibility.ResidentStatus'] = "VAResident"
        else:
            self.add_error('You must be a legal resident of Virginia.', field='legal_resident')

        if user.get('has_previous_state'):
            form['Eligibility.RegisteredInAnotherState'] = "true"  # note lack of capitalization here, field values are case sensitive
            form['Eligibility.PreviousRegisteredState'] = user.get('previous_state')
        else:
            form['Eligibility.RegisteredInAnotherState'] = "false"

        if user.get('disenfranchised'):
            self.add_error('You must not have been convicted of a felony or disqualified to vote.', field='disenfranchised')
        if user.get('incompetent'):
            self.add_error('You must not have been judged mentally incompetent to register to vote.', field='incompetent')

        # Have you ever been convicted of a felony or judged mentally incapacitated and disqualified to vote?
        if (not user.get('disenfranchised')) and (not user.get('incompetent')):
            form['Eligibility.IsProhibited'] = "False"
        else:
            form['Eligibility.IsProhibited'] = "True"

        self.browser.submit_form(form)

    def voting_identity(self, user, form):
        if user.get('privacy_notice'):
            form['Identity.HasReadPrivacyActNotice'] = "true"
        else:
            self.add_error('You must agree to have read the privacy notice', field='privacy_notice')

        form['Identity.FirstName'].value = user['first_name']
        if user.get('middle_name'):
            form['Identity.MiddleName'].value = user['middle_name']
        else:
            form['Identity.NoMiddleName'] = "true"
        form['Identity.LastName'].value = user['last_name']
        if user.get('suffix'):
            form['Identity.Suffix'].value = user['suffix']
        else:
            form['Identity.NoSuffix'] = "true"

        (year, month, day) = split_date(user['date_of_birth'])
        form['Identity.DateOfBirth'].value = '/'.join([month, day, year])

        # values need to be M/F
        form['Identity.Gender'].value = parse_gender(user['gender'])

        if user.get('ssn') == "NONE":
            form['Identity.DoesNotHaveSocialSecurityNumber'] = "true"
        else:
            form['Identity.SocialSecurityNumber'] = user.get('ssn')

        if user.get('state_id_number') and user.get('consent_use_signature'):
            form['Identity.DmvConsent'] = "Consent"
            form['Identity.DmvNumber'] = user.get('state_id_number').replace('-', '')
        elif not user.get('consent_use_signature'):
            form['Identity.DmvConsent'] = "Decline"
        elif not user.get('state_id_number'):
            form['Identity.DmvConsent'] = "DoNotHave"

        self.browser.submit_form(form)

    def protected_voter(self, user, form):
        # Does user legally qualify to have my residence address not published on publicly-released voter lists.
        # I (or a member of my household) claim one of the four reasons:
        # - Active or retired law enforcement officer, judge, U.S. or Virginia Attorney General attorney
        # - Have a court-issued protective order for my benefit
        # - Have a complaint with law enforcement about being threatened or stalked (You must attach a copy of the complaint that you filed with your registration).
        # - Registered with the Virginia Attorney General's Address Confidentiality Program

        # default - I do not legally qualify
        form['ProtectedVoter.ProtectedVoter'] = ''

        self.browser.submit_form(form)

    def overseas_classification(self, user, form):
        # Classification
        # I am a member of the Uniformed Services or Merchant Marines on active duty and absent from my voting district.
        # I am a spouse or dependent of a member of the Uniformed Services or Merchant Marines on active duty and absent from my voting district.
        
        if user.get('military_or_overseas'):
            if user['military_or_overseas'] == 'military':
                form['Classification.WithinUs'] = 1
            elif user['military_or_overseas'] == 'spouse_dependent':
                form['Classification.WithinUs'] = 2
        else:
            form['Classification.WithinUs'] = "Neither"
        self.browser.submit_form(form)

    def absentee_ballot(self, user, form):
        if user.get('vote_by_mail'):
            #  I have a reason or condition that prevents me from going to the polls on Election Day.
            form['Absentee.AbsenteeRequestType'] = "SBE 701"
        else:
            form['Absentee.AbsenteeRequestType'] = 'na'
        self.browser.submit_form(form)

    def get_locality_fips(self, user):
        # get locality fips ID by address from elsewhere on virginia.gov
        locality_browser = RoboBrowser(parser='html.parser', user_agent='HelloVote.org', history=True)
        locality_browser.open('http://www.tax.virginia.gov/fips')
        locality_form = locality_browser.get_form(id="build-fips-form")
        locality_form['street1'] = user['address']
        locality_form['city'] = user['city']
        locality_form['zipcode'] = user['zip']
        locality_form['zipcodeext'] = ''
        # two 'op' buttons, submit & reset. thankfully submit is first.
        locality_browser.submit_form(locality_form, submit=locality_form['op'])
        return locality_browser.select('dl.dl-horizontal dd')[1].text.strip().upper()

    def residence_address(self, user, form):
        # form is prefilled with info from DMV
        # overwrite with info from hellovote
        form['CurrentAddress.Address.Line1'] = user.get('address').upper()
        form['CurrentAddress.Address.Line2'] = user.get('address_unit', '')
        form['CurrentAddress.Address.City'] = user.get('city').upper()
        form['CurrentAddress.Address.ZipCode'] = user.get('zip')

        # try to match locality by county name
        locality = user.get('county').upper()
        locality_options = options_dict(form['CurrentAddress.Address.LocalityUId'])
        if locality in locality_options:
            form['CurrentAddress.Address.LocalityUId'] = locality_options[locality]
        else:
            locality = locality + " COUNTY"
            form['CurrentAddress.Address.LocalityUId'] = locality_options[locality]
        self.browser.submit_form(form)

    def contact_information(self, user, form):
        if user.get('email'):
            form['ContactInformation.EmailAddress'] = user.get('email', '')
            form['ContactInformation.EmailContactPreference'] = ''

        form['ContactInformation.PhoneNumber'] = user.get('phone', '')

        # this appears to be required
        form['Assistant.InterestedInElectionOfficial'] = 'false'

        self.browser.submit_form(form)

    def affirmation(self, user, form):
        #  I swear/affirm, under felony penalty for making willfully false material statements or entries, that the information provided on this form is true. I authorize the cancellation of my current registration.
        if user.get('confirm_name_address') and user.get('authorize_cancellation'):
            form['VoterRegistrationAffirmation'] = 'true'
        self.browser.submit_form(form)

