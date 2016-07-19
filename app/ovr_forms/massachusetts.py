from base_ovr_form import BaseOVRForm, OVRError
from form_utils import get_address_components, options_dict, split_date


class Massachusetts(BaseOVRForm):

    def __init__(self):
        super(Massachusetts, self).__init__('https://www.sec.state.ma.us/OVR/Pages/MinRequirements.aspx?RMVId=True')
        self.add_required_fields(['will_be_18', 'legal_resident', 'consent_use_signature',
            'political_party', 'not_under_guardianship', 'not_disqualified'])

    def parse_errors(self):
        messages = []
        for error in self.browser.select('.ErrorMessage li'):
            messages.append(error.text)
        return messages

    def submit(self, user):

        self.validate(user)

        # format is: [kwargs to select / identify form, method to call with form]
        # frustratingly, MA uses the same methods and IDs for each form...
        forms = [
            [{'action': "./MinRequirements.aspx?RMVId=True"}, self.minimum_requirements],
            [{'action': "./FormAndReview.aspx?RMVId=True"}, self.rmv_identification],
            [{'action': "./FormAndReview.aspx?RMVId=True"}, self.complete_form],
            [{'action': "./FormAndReview.aspx?RMVId=True"}, self.review]
        ]

        for form_kwargs, handler in forms:

            step_form = self.browser.get_form(**form_kwargs)

            if step_form:
                handler(user, step_form)
                errors = self.parse_errors()

                if errors:
                    return {'status': 'error', 'errors': errors}
            else:
                return {'status': 'error'}

        return {'status': 'OK'}

    def minimum_requirements(self, user, form):

        if user['us_citizen']:
            form['ctl00$MainContent$ChkCitizen'].checked = 'checked'
            form['ctl00$MainContent$ChkCitizen'].value = 'on'

        else:
            raise OVRError('You must be a U.S. Citizen.', field='us_citizen')

        if user['will_be_18']:
            form['ctl00$MainContent$ChkAge'].checked = 'checked'
            form['ctl00$MainContent$ChkAge'].value = 'on'

        else:
            raise OVRError('You must be 18 by Election Day.', field='will_be_18')

        if user['legal_resident']:
            form['ctl00$MainContent$ChkResident'].checked = 'checked'
            form['ctl00$MainContent$ChkResident'].value = 'on'

        else:
            raise OVRError('You must be a Massachusetts resident.', field='legal_resident')

        self.browser.submit_form(form, submit=form['ctl00$MainContent$BtnBeginOVR'])

        if 'You must meet all 3 requirements' in self.browser.response.text:
            raise OVRError('You must meet all three requirements: you are a U.S. citizen, you will be 18 on or before Election Day, and you are a Massachusetts resident')

    def rmv_identification(self, user, form):
        form['ctl00$MainContent$TxtFirstName'].value = user['first_name']
        form['ctl00$MainContent$TxtLastName'].value = user['last_name']

        (year, month, day) = split_date(user['date_of_birth'])
        form['ctl00$MainContent$TxtDoB'].value = '/'.join([month, day, year])

        form['ctl00$MainContent$TxtRMVID'].value = user['id_number']
        
        if user['consent_use_signature']:
            form['ctl00$MainContent$ChkConsent'].checked = 'checked'
            form['ctl00$MainContent$ChkConsent'].value = 'on'

        else:
            raise OVRError("You must consent to using your signature from the Massachusetts RMV.", field='consent_use_signature')

        self.browser.submit_form(form, submit=form['ctl00$MainContent$BtnValidate'])

        if "Your RMV ID cannot be verified" in self.browser.response.text:
            raise OVRError("Your Massachusetts RMV ID cannot be verified.", field='id_number')
            # todo: fall back to PDF form here? retry?

    def complete_form(self, user, form):

        address_components = get_address_components(user['home_address'], user['home_city'], user['state'], user['home_zip'])

        form['ctl00$MainContent$txtStNum'].value = address_components['primary_number']
        form['ctl00$MainContent$txStNameSuffix'].value = address_components['street_name']

        # todo: these two seem fraught for IndexErrors
        form['ctl00$MainContent$ddlStreetSuffix'].value = options_dict(form['ctl00$MainContent$ddlStreetSuffix'])[address_components['street_suffix'].upper()]
        form['ctl00$MainContent$ddlCityTown'].value = options_dict(form['ctl00$MainContent$ddlCityTown'])[user['home_city']]

        form['ctl00$MainContent$txtZip'].value = user['home_zip']

        party = user['political_party']

        if party and party.lower() != 'independent':

            parties = options_dict(form['ctl00$MainContent$ddlPartyList'])
            designations = options_dict(form['ctl00$MainContent$ddlPoliticalDesig'])

            if party in parties:
                form['ctl00$MainContent$PartyEnrolled'].value ='rdoBtnParty'
                # crucial - un-disable the party list
                del self.browser.select('select[name="ctl00$MainContent$ddlPartyList"]')[0]['disabled']
                form['ctl00$MainContent$ddlPartyList'].value = parties[party]

            
            elif party in designations:
                form['ctl00$MainContent$PartyEnrolled'].value = 'rdoBtnPolDesig'
                # crucial - un-disable the designation list
                del self.browser.select('select[name="ctl00$MainContent$ddlPoliticalDesig"]')[0]['disabled']
                form['ctl00$MainContent$ddlPoliticalDesig'].value = designations[party]
            
        else:
            # No Party (Unenrolled, commonly referred to as ''Independent'')
            form['ctl00$MainContent$PartyEnrolled'].value = 'rdoBtnNoParty'
        

        # possible todos, all optional:
        # former name
        # separate mailing address
        # phone number
        # address where you were last registered to vote.

        self.browser.submit_form(form)

    def review(self, user, form):

        # I hereby swear (affirm) that I am the person named above, that the
        # above information is true, that I AM A CITIZEN OF THE UNITED STATES,
        # that I am not a person under guardianship which prohibits my
        # registering to vote, that I am not temporarily or permanantly
        # disqualified by law from voting because of corrupt practices in
        # respect to elections, that I am not currently incarcerated for a
        # felony conviction, and that I consider this residence to be my home.

        if user['us_citizen'] and user['not_a_felon'] and user['legal_resident'] \
            and user['not_under_guardianship'] and user['not_disqualified']:

            form['ctl00$MainContent$ChkIsSwear'].checked = 'checked'
            form['ctl00$MainContent$ChkIsSwear'].value = 'on'

        elif not user['us_citizen']:
            raise OVRError("You must be a U.S. Citizen.", field='us_citizen')

        elif not user['not_a_felon']:
            raise OVRError("You must not be a felon.", field='not_a_felon')

        elif not user['legal_resident']:
            raise OVRError("You must be a Massachusetts resident.", field='legal_resident')

        elif not user['not_under_guardianship']:
            raise OVRError("You must not be under guardianship which prohibits your registering to vote.", field='not_under_guardianship')

        elif not user['not_disqualified']:
            raise OVRError("You must not be legally disqualified to vote.", field='not_disqualified')

        # self.browser.submit_form(review_form)


