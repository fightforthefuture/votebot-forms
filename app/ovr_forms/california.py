from base_ovr_form import BaseOVRForm
from form_utils import bool_to_string, split_date, options_dict, get_party_from_list, clean_browser_response


class California(BaseOVRForm):
    def __init__(self):
        super(California, self).__init__('https://covr.sos.ca.gov/?language=en-US')
        self.add_required_fields(['will_be_18', 'political_party', 'disenfranchised',
                                 'ssn_last4', 'county', 'consent_use_signature'])
        self.success_string = "Your voter registration application is now complete."

    def submit(self, user):
        # dict loses its order when iteritem()'ing
        # there are probably more elegant approaches than lists,
        # but for now...
        forms = [
                    ['/?language=en-US', self.step1],
                    ['/Home/MainForm', self.step2],
                    ['/Home/MainForm2', self.step3],
                    ['/Home/Review', self.step4],
                    ['/Home/Confirmation', self.step5]
                ]

        for action, function in forms:
            step_form = self.browser.get_form(action=action)
            if step_form:
                function(step_form, user)
            else:
                return {'status': 'error', 'errors': self.parse_errors()}

        success_page = clean_browser_response(self.browser)
        if self.success_string in success_page:
            return {'status': 'success'}
        else:
            # TODO, handle gracefully
            return {'status': 'failure'}

    def parse_errors(self):
        errors_dict = {}
        for error in self.browser.find_all(class_='field-validation-error'):
            errors_dict[error['data-valmsg-for']] = error.text
        return errors_dict

    def step1(self, form, user):
        form['VoterType'].value = 'A001'  # default check 'A California resident living in the United States.'
        self.browser.submit_form(form)

        #  TODO, do we have to check against others voter types?
        #  A California resident living in the United States.
        #  A member of the Uniformed Services or Merchant Marine on active duty outside my county.
        #  An eligible spouse or dependent of a member of the Uniformed Services or Merchant Marine on active duty outside my county.
        #  An activated National Guard member on State orders outside my county.
        #  A U.S. citizen residing outside the U.S. temporarily.
        #  A U.S. citizen residing outside the U.S. indefinitely.
        #  A U.S. citizen and have never resided in the U.S.

    def step2(self, form, user):

        # doctor up the DOM to un-disable Political Party
        del self.browser.select('select[name="VoterInformation.PoliticalPartyIdKey"]')[0]['disabled']

        #  Eligibility
        form['VoterInformation.IsUsCitizen'].value = bool_to_string(user['us_citizen'])
        form['VoterInformation.IsEighteenYear'].value = bool_to_string(user['will_be_18'])

        prefix_options = options_dict(form['VoterInformation.PrefixIdKey'])
        if 'name_prefix' in user:
            form['VoterInformation.PrefixIdKey'].value = prefix_options.get(user['name_prefix'])
        form['VoterInformation.NameFirst'].value = user['first_name']
        form['VoterInformation.NameMiddle'].value = user.get('middle_name')
        form['VoterInformation.NameLast'].value = user['last_name']
        suffix_options = options_dict(form['VoterInformation.SuffixIdKey'])
        if 'name_suffix' in user:
            form['VoterInformation.SuffixIdKey'].value = suffix_options.get(user['name_suffix'])

        form['VoterInformation.EmailId'].value = user.get('email', '')
        form['VoterInformation.ConfirmEmailId'].value = user.get('email', '')
        #form['VoterInformation.PhoneNumber].value'] = user.get('phone', '')

        (year, month, day) = split_date(user['date_of_birth'], padding=False)
        form['VoterInformation.Month'].value = month
        form['VoterInformation.Day'].value = day
        form['VoterInformation.Year'].value = year

        #  ID and last 4 of SSN (CA requires both!)
        if 'state_id_number' in user:
            form['VoterInformation.CaIdentification'].value = user.get('state_id_number')
        else:
            form['VoterInformation.NoCaIdentification'].value = bool_to_string(True)
            # we actually require this, so shouldn't get here, but just in case
        if user.get('ssn_last4') == "NONE":
            form['VoterInformation.NoSsnLastFour'].value = bool_to_string(True)
        else:
            form['VoterInformation.SsnLastFour'].value = user.get('ssn_last4')

        #  Home and Mailing Address
        form['VoterInformation.AddressStreet1'].value = user['address']
        form['VoterInformation.AddressStreet2'].value = user.get('apartment')
        form['VoterInformation.AddressCity'].value = user['city']
        form['VoterInformation.AddressZip'].value = user['zip']
        county_options = options_dict(form['VoterInformation.CountyIdKey'])
        form['VoterInformation.CountyIdKey'].value = county_options.get(user['county'])

        # Ethnicity (optional)
        if 'ethnicity' in user:
            ethnicity_options = options_dict(form['VoterInformation.EthnicityIdKey'])
            form['VoterInformation.EthnicityIdKey'].value = ethnicity_options.get(user['ethnicity'],
                                                                                       ethnicity_options['Other'])

        #  Political Party Preference
        if user['political_party'] is 'No party preference':
            form['VoterInformation.isPoliticalPrefSelected'].value = bool_to_string(False, capitalize=True)
        else:
            form['VoterInformation.isPoliticalPrefSelected'].value = bool_to_string(True, capitalize=True)
            party_options = options_dict(form['VoterInformation.PoliticalPartyIdKey'])
            # do fuzzy match to political party options
            party_choice = get_party_from_list(user['political_party'], party_options.keys())

            if party_choice in party_options.keys():
                form['VoterInformation.PoliticalPartyIdKey'].value = party_options[party_choice]
            else:
                form['VoterInformation.PoliticalPartyIdKey'].value = party_options.get('Other')
                form['VoterInformation.PoliticalPrefOther'].value = user['political_party']

        next_button = form['command']
        next_button.value = 'Next'
        
        self.browser.submit_form(form, submit=next_button)

    def step3(self, form, user):
        #  Vote by Mail
        form['VoterInformation.IsVoteByMail'].value = bool_to_string(user.get('vote_by_mail', False))

        #  Consent to Use Signature
        form['VoterInformation.IsDmvSignatureConsent'].value = bool_to_string(user['consent_use_signature'])

        #  Affirmation
        user_is_eligible = user['us_citizen'] and user['will_be_18'] and (not user['disenfranchised'])
        
        # also add "information is true and correct"?
        form['VoterInformation.isAffirmationSelected'].value = bool_to_string(user_is_eligible)
        form['VoterInformation.isAffirmationSelected'].checked = 'checked'

        # seemingly very redundant, but in testing, curl's failed without these:
        form['VoterInformation.IsAPollWorker'].value = 'false'
        form['VoterInformation.MultiLanguageList[0].IsSelected'].value = 'false'
        form['VoterInformation.MultiLanguageList[1].IsSelected'].value = 'false'
        form['VoterInformation.MultiLanguageList[2].IsSelected'].value = 'false'
        form['VoterInformation.MultiLanguageList[3].IsSelected'].value = 'false'
        form['VoterInformation.MultiLanguageList[4].IsSelected'].value = 'false'
        form['VoterInformation.MultiLanguageList[5].IsSelected'].value = 'false'
        form['VoterInformation.MultiLanguageList[6].IsSelected'].value = 'false'
        form['VoterInformation.MultiLanguageList[7].IsSelected'].value = 'false'
        form['VoterInformation.MultiLanguageList[8].IsSelected'].value = 'false'
        form['VoterInformation.MultiLanguageList[9].IsSelected'].value = 'false'
        form['VoterInformation.MultiLanguageList[10].IsSelected'].value = 'false'
        form['VoterInformation.IsPollingPlaceProvided'].value = 'false'

        next_button = form['command']
        next_button.value = 'Next'
        self.browser.submit_form(form, submit=next_button)

    def step4(self, form, user):
        submit_button = form['command']
        submit_button.value = 'Submit'
        self.browser.submit_form(form, submit=submit_button)

    def step5(self, form, user):
        # Send an email receipt from the state
        form['email'] = user['email']
        self.browser.submit_form(form)
