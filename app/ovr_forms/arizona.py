from base_ovr_form import BaseOVRForm, OVRError
from form_utils import (ValidationError, clean_browser_response, options_dict, split_date, get_party_from_list)
from form_address import (get_address_from_freeform, get_street_address_from_components)
import sys, traceback


class Arizona(BaseOVRForm):

    def __init__(self):
        super(Arizona, self).__init__('https://servicearizona.com/webapp/evoter/selectLanguage')
        self.add_required_fields(['will_be_18', 'legal_resident', 'incompetent', 'disenfranchised', 'ssn_last4', 'has_separate_mailing_address', 'political_party'])
        self.success_string = 'Your application for voter registration has been successfully completed.'

    def submit(self, user, error_callback_url=None):
        self.set_user_agent(user)
        self.error_callback_url = error_callback_url

        try:
            forms = [
                self.language,
                self.init_voter_registration,
                self.eligibility,
                self.personal_information,
                self.change_of_address,
                self.update_address,
                self.confirm_address,
                self.register_to_vote,
                self.verify_voter_registration,
                self.vote_by_mail
            ]

            for handler in forms:
                handler(user)
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

    def parse_errors(self):
        if self.errors:
            return self.errors
        messages = []
        errorSel = ['.formError', '.pageError']
        for selector in errorSel:
            for error in self.browser.select(selector):
                messages.append({'error': error.text})
        return messages

    def get_default_submit_headers(self):
        # AZ does a validation check on referer, so fill it in with the current URL
        return {'Referer': self.browser.url}

    def language(self, user):
        language_form = self.browser.get_form()
        language_form['lang'].value = 'en'
        self.browser.submit_form(language_form, headers=self.get_default_submit_headers())

    def init_voter_registration(self, user):
        # a functional no-op; just click submit.
        voter_reg_form = self.browser.get_form()
        self.browser.submit_form(voter_reg_form, headers=self.get_default_submit_headers())

    def eligibility(self, user):
        eligibility_form = self.browser.get_form()
        
        # they have some Dojo trickery, and server-side validation to go with it?
        # it needs both checked and a value set. :shrug:
        eligibility_form['resident'].checked = 'checked' if user['legal_resident'] else ''
        eligibility_form['resident'].value = 'true' if user['legal_resident'] else 'false'
        
        eligibility_form['felon'].checked = 'checked' if not user['disenfranchised'] else ''
        eligibility_form['felon'].value = 'true' if not user['disenfranchised'] else 'false'
        
        eligibility_form['competent'].checked = 'checked' if not user['incompetent'] else ''
        eligibility_form['competent'].value = 'true' if not user['incompetent'] else 'false'
        
        # these are more straightforward
        eligibility_form['citizenCheck'].value = 'on' if user['us_citizen'] else 'no'
        eligibility_form['ageCheck'].value = 'on' if user['will_be_18'] else 'no'
        
        self.browser.submit_form(eligibility_form, headers=self.get_default_submit_headers())

    def personal_information(self, user):
        personal_info_form = self.browser.get_form()
        personal_info_form['firstname'].value = user['first_name']
        personal_info_form['lastname'].value = user['last_name']

        year, month, day = split_date(user['date_of_birth'])
        personal_info_form['dob'].value = '/'.join([month, day, year])

        personal_info_form['ssn3'].value = user['ssn_last4']
        personal_info_form['dln'].value = user['state_id_number']

        # specify the Continue button, not the "what if I don't know my DL number?" button, also a submit
        self.browser.submit_form(personal_info_form, submit=personal_info_form['_eventId_continue'], headers=self.get_default_submit_headers())

    def change_of_address(self, user):
        frm = self.browser.get_form()

        frm['resChange'].value = 'C'

        # user has different residential and mailing addresses on file with MVD
        if "C" in frm['mailChange'].options:
            if user['has_separate_mailing_address']:
                frm['mailChange'].value = 'C'
            else:
                frm['mailChange'].value = 'D'
        else:
            if user['has_separate_mailing_address']:
                frm['mailChange'].value = 'A'
            else:
                frm['mailChange'].value = 'N'

        self.browser.submit_form(frm, submit=frm['_eventId_continue'], headers=self.get_default_submit_headers())
    
    def update_address(self, user):
        frm = self.browser.get_form()
        print frm

        frm['resAddr'].value = user['address']
        frm['resCity'].value = user['city']
        frm['resState'].value = "AZ"
        frm['resZip1'].value = user['zip']

        if user['has_separate_mailing_address']:
            address = get_address_from_freeform(user['separate_mailing_address'])
            address_components = address['components']

            mailing_address = get_street_address_from_components(address_components)

            frm['mailAddr'].value = mailing_address
            frm['mailCity'].value = address_components['city_name']
            frm['mailState'].value = address_components['state_abbreviation']
            frm['mailZip1'].value = address_components['zipcode']

        self.browser.submit_form(frm, submit=frm['_eventId_update'], headers=self.get_default_submit_headers())

    def confirm_address(self, user):
        frm = self.browser.get_form()

        self.browser.submit_form(frm, submit=frm['_eventId_continue'], headers=self.get_default_submit_headers())

    def register_to_vote(self, user):
        frm = self.browser.get_form()

        user["political_party"] = user["political_party"].strip()

        if user['political_party'].lower() == 'independent' or user['political_party'].lower() == "none":
            frm['partyPreference'].value = "No Party Preference"

        else:
            party_options = options_dict(frm['partyPreference'])
            # do fuzzy match to political party options
            party_choice = get_party_from_list(user['political_party'], party_options.keys())

            if party_choice in party_options.keys():
                frm['partyPreference'].value = party_options[party_choice]
            else:
                frm['otherPartyPreference'].value = user['political_party']

        frm['email'].value = user['email']

        self.browser.submit_form(frm, submit=frm['_eventId_register'], headers=self.get_default_submit_headers())

    def verify_voter_registration(self, user):
        frm = self.browser.get_form()
        self.browser.submit_form(frm, submit=frm['_eventId_finish'], headers=self.get_default_submit_headers())

    def vote_by_mail(self, user):
        frm = self.browser.get_form()
        if user.get('vote_by_mail'):
            submit_choice = frm['_eventId_votemail']
        else:
            submit_choice = frm['_eventId_votepolls']
        self.browser.submit_form(frm, submit=submit_choice, headers=self.get_default_submit_headers())
