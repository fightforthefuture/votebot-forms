from base_ovr_form import BaseOVRForm, OVRError
from form_utils import bool_to_string, options_dict, split_date, get_party_from_list


class Colorado(BaseOVRForm):
    def __init__(self):
        super(Colorado, self).__init__('https://www.sos.state.co.us/voter-classic/pages/pub/olvr/verifyNewVoter.xhtml')
        self.add_required_fields(['is_military', 'vote_by_mail', 'political_party', 'email',
                'military_overseas', 'gender', 'legal_resident', 'consent_use_signature',
                'will_be_18', 'eligible_and_providing_accurate_information'])

    def submit(self, user):

        self.validate(user)

        # format is: [kwargs to select / identify form, method to call with form]
        forms = [
            [{'id': 'verifyNewVoterForm'}, self.verify_identification],
            [{'id': 'editVoterForm'}, self.edit_voter_information],
            [{'id': 'reviewVoterForm'}, self.review],
            [{'id': 'affirmationVoterForm'}, self.affirmation]
        ]

        for form_kwargs, handler in forms:

            step_form = self.browser.get_form(**form_kwargs)

            if step_form:
                handler(user, step_form)

            errors = self.parse_errors()

            if errors or not step_form:
                return {'errors': errors}

        return {'status': 'OK'}

    def parse_errors(self):
        if self.errors:
            return self.errors

        messages = []
        for error in self.browser.select('.ui-messages-error-summary'):
            messages.append({'error': error.text})
        return messages

    def verify_identification(self, user, form):

        form['verifyNewVoterForm:voterSearchLastId'].value = user['last_name']
        form['verifyNewVoterForm:voterSearchFirstId'].value = user['first_name']

        (year, month, day) = split_date(user['date_of_birth'])
        form['verifyNewVoterForm:voterDOB'].value = '/'.join([month, day, year])

        form['verifyNewVoterForm:driverId'].value = user['state_id_number']

        self.browser.submit_form(form, submit=form['verifyNewVoterForm:voterSearchButtonId'])

        if 'We can\'t find a record that matches your information' in self.browser.response.text:

            # todo: this really needs to be able to accommodate several fields.
            self.add_error('We could not find your record. Please double-check your first name, last name, date of birth, and driver\'s license number.', field='state_id_number')
            # todo: other calls to action, from the site:
            # Call Colorado SOS: 303-894-2200
            # Fill out CO's PDF: http://www.sos.state.co.us/pubs/elections/vote/VoterRegFormEnglish.pdf

    def edit_voter_information(self, user, form):

        party = get_party_from_list(user['political_party'], options_dict(form['editVoterForm:partyAffiliationId_input']))
        
        # it is required. if we haven't found a match, defer to 'Unaffiliated'
        if not party:
            party = 'Unaffiliated'
        
        form['editVoterForm:partyAffiliationId_input'].value = options_dict(form['editVoterForm:partyAffiliationId_input'])[party]

        if user['is_military'] or user['military_overseas']:
            form['editVoterForm:areUOCAVAId'].value = 'Y'
            form['editVoterForm:uocavaTypeId'].value = 'a' if user['is_military'] else 'c'
        else:
            form['editVoterForm:areUOCAVAId'].value = 'N'

        form['editVoterForm:uocavaBallotMethodId'].value = 'Mail' if user['vote_by_mail'] else 'Email' # or 'Fax'

        # todo: these seem optional or debatable
        # email, phone and gender are prefilled
        form['editVoterForm:emailId'].value = user['email']
        if user['receive_election_info_by_email']:
            form['editVoterForm:receiveEmailCommunicationId'].checked = 'checked'
        form['editVoterForm:phoneId'].value = user['phone']
        form['editVoterForm:genderSelectId'].value = '0' if user['gender'] == 'F' else '1'

        form['editVoterForm:resAddress'].value = user['address']
        form['editVoterForm:resCity'].value = user['city']

        form['editVoterForm:resCounty_input'].value = options_dict(form['editVoterForm:resCounty_input'])[user['county']]

        form['editVoterForm:resZip'].value = user['zip']

        self.browser.submit_form(form, submit=form['editVoterForm:j_idt113'])

    def review(self, user, form):
        # noop
        self.browser.submit_form(form, submit=form['reviewVoterForm:j_idt86'])

    def affirmation(self, user, form):
        # this field name jumps out at me...

        # I am aware that if I
        # register to vote in Colorado I am also considered a resident
        # of Colorado for motor vehicle registration and operation
        # purposes and for income tax purposes.
        if user['legal_resident']:
            form['affirmationVoterForm:crimminalActId'].checked = 'checked'
        else:
            self.add_error('You must be a legal resident of Colorado.', field='legal_resident')


        # I might want some help dicing this up into fields:
        
        # I affirm that I am a citizen of the United States; I have been a
        # resident of the state of Colorado for at least twenty-two
        # days immediately prior to an election in which I intend to
        # vote; and I am at least sixteen years old and understand
        # that I must be eighteen years old to be eligible to vote. I
        # further affirm that my present address as stated herein is
        # my sole legal place of residence, that I claim no other
        # place as my legal residence, and that I understand that I am
        # committing a felony if I knowingly give false information
        # regarding my place of present residence. I certify under
        # penalty of perjury that I meet the registration
        # qualifications; that the information I have provided on this
        # application is true to the best of my knowledge and belief;
        # and that I have not, nor will I, cast more than one ballot
        # in any election.
        if user['will_be_18'] and user['legal_resident'] and user['eligible_and_providing_accurate_information']:
            form['affirmationVoterForm:affirmCtizId'].checked = 'checked'
        else:
            
            if not user['will_be_18']:
                self.add_error('You must be 18 by Election Day in order to register to vote.', field='will_be_18')

            if not user['eligible_and_providing_accurate_information']:
                self.add_error('You must be eligible to vote and provide accurate information in order to register.', field='eligible_and_providing_accurate_information')

        if user['consent_use_signature']:
            form['affirmationVoterForm:fromStatueId'].checked = 'checked'
        else:
            self.add_error('You must consent to using your signature', field='consent_use_signature')

        # self.browser.submit_form(form, submit=form['affirmationVoterForm:j_idt73'])






