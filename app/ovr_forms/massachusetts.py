from base_ovr_form import BaseOVRForm, OVRError
from form_utils import (ValidationError, clean_browser_response, options_dict,
                        split_date, split_name, get_party_from_list)
from form_address import (get_address_components, get_address_from_freeform,
                        get_street_name_from_components, get_street_address_from_components,
                        get_address_unit_from_components)
import json
import sys, traceback

MA_ARCHAIC_COMMUNITIES = json.load(open('app/ovr_forms/massachusetts_data.json', 'r'))['archaic']


class Massachusetts(BaseOVRForm):

    def __init__(self):
        super(Massachusetts, self).__init__('https://www.sec.state.ma.us/OVR/Pages/MinRequirements.aspx?RMVId=True')
        self.add_required_fields(['will_be_18', 'legal_resident', 'consent_use_signature',
            'political_party', 'disenfranchised', 'disqualified'])
        self.success_string = 'Your application for voter registration has been transmitted'
        # careful of trailing spaces, that paragraph is hard wrapped

    def parse_errors(self):
        if self.errors:
            return self.errors

        messages = []
        for error in self.browser.select('.ErrorMessage li'):
            messages.append({'error': error.text})
        return messages

    def submit(self, user, error_callback_url=None):
        self.set_user_agent(user)
        self.error_callback_url = error_callback_url

        try:
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
            raise OVRError(self, message="%s %s" % (ex_type, ex), payload=traceback.format_tb(tb), error_callback_url=self.error_callback_url)

    def minimum_requirements(self, user, form):

        if user['us_citizen']:
            form['ctl00$MainContent$ChkCitizen'].checked = 'checked'
            form['ctl00$MainContent$ChkCitizen'].value = 'on'

        else:
            self.add_error('You must be a U.S. Citizen.', field='us_citizen')

        if user['will_be_18']:
            form['ctl00$MainContent$ChkAge'].checked = 'checked'
            form['ctl00$MainContent$ChkAge'].value = 'on'

        else:
            self.add_error('You must be 18 by Election Day.', field='will_be_18')

        if user['legal_resident']:
            form['ctl00$MainContent$ChkResident'].checked = 'checked'
            form['ctl00$MainContent$ChkResident'].value = 'on'

        else:
            self.add_error('You must be a Massachusetts resident.', field='legal_resident')

        self.browser.submit_form(form, submit=form['ctl00$MainContent$BtnBeginOVR'])

        # if 'You must meet all 3 requirements' in self.browser.response.text:
        #     self.add_error('You must meet all three requirements: you are a U.S. citizen, you will be 18 on or before Election Day, and you are a Massachusetts resident')

    def rmv_identification(self, user, form):
        form['ctl00$MainContent$TxtFirstName'].value = user['first_name']
        form['ctl00$MainContent$TxtLastName'].value = user['last_name']

        (year, month, day) = split_date(user['date_of_birth'])
        form['ctl00$MainContent$TxtDoB'].value = '/'.join([month, day, year])

        form['ctl00$MainContent$TxtRMVID'].value = user['state_id_number']

        if user['consent_use_signature']:
            form['ctl00$MainContent$ChkConsent'].checked = 'checked'
            form['ctl00$MainContent$ChkConsent'].value = 'on'

        else:
            self.add_error("You must consent to using your signature from the Massachusetts RMV.", field='consent_use_signature')

        self.browser.submit_form(form, submit=form['ctl00$MainContent$BtnValidate'])

        if "Your RMV ID cannot be verified" in self.browser.response.text:
            self.add_error("Your Massachusetts RMV ID cannot be verified.", field='state_id_number')

    def complete_form(self, user, form):

        address_components = get_address_components(user['address'], user['city'], user['state'], user['zip'])

        form['ctl00$MainContent$txtStNum'].value = address_components['primary_number']
        street_name = get_street_name_from_components(address_components)
        form['ctl00$MainContent$txStNameSuffix'].value = street_name[:25]

        if user.get('address_unit') and not user.get('address_unit').lower() == "none":
            form['ctl00$MainContent$txtUnitApt'].value = user.get('address_unit')

        if 'street_suffix' in address_components:
            street_suffix_options = options_dict(form['ctl00$MainContent$ddlStreetSuffix'])
            try:
                form['ctl00$MainContent$ddlStreetSuffix'].value = street_suffix_options[address_components['street_suffix'].upper()]
            except KeyError:
                form['ctl00$MainContent$ddlStreetSuffix'].value = street_suffix_options['No suffix']

        form['ctl00$MainContent$ddlCityTown'].value = options_dict(form['ctl00$MainContent$ddlCityTown'])[user['city']]
        city_normalized = MA_ARCHAIC_COMMUNITIES.get(user['city'], user['city'])
        try:
            form['ctl00$MainContent$ddlCityTown'].value = options_dict(form['ctl00$MainContent$ddlCityTown'])[city_normalized]
        except KeyError:
            raise ValidationError(message='unable to find city in CityTown list', payload=user['city'])

        form['ctl00$MainContent$txtZip'].value = user['zip']

        user_party = user['political_party'].strip()
        parties = options_dict(form['ctl00$MainContent$ddlPartyList'])
        designations = options_dict(form['ctl00$MainContent$ddlPoliticalDesig'])

        party = get_party_from_list(user_party, parties.keys())
        designation = get_party_from_list(user_party, designations.keys())

        user_party = user_party.lower()

        if user_party and user_party != 'independent' and user_party != 'none':

            if party:
                form['ctl00$MainContent$PartyEnrolled'].value = 'rdoBtnParty'
                # crucial - un-disable the party list
                del self.browser.select('select[name="ctl00$MainContent$ddlPartyList"]')[0]['disabled']
                form['ctl00$MainContent$ddlPartyList'].value = parties[party]

            elif designation:
                form['ctl00$MainContent$PartyEnrolled'].value = 'rdoBtnPolDesig'
                # crucial - un-disable the designation list
                del self.browser.select('select[name="ctl00$MainContent$ddlPoliticalDesig"]')[0]['disabled']
                form['ctl00$MainContent$ddlPoliticalDesig'].value = designations[designation]

            else:
                # unable to match designation, unenrolled
                self.add_error("We were unable to match that political designation", field='political_party')
                form['ctl00$MainContent$PartyEnrolled'].value = 'rdoBtnNoParty'

        else:
            # No Party (Unenrolled, commonly referred to as ''Independent'')
            form['ctl00$MainContent$PartyEnrolled'].value = 'rdoBtnNoParty'

        # phone number, optional
        if user.get('phone'):
            phone = user.get('phone').replace('+1', '')
            form['ctl00$MainContent$txtAreaCode'] = phone[0:3]
            form['ctl00$MainContent$txtPhone3'] = phone[3:6]
            form['ctl00$MainContent$txtPhone4'] = phone[6:10]

        # separate mailing address
        if user.get('has_separate_mailing_address'):
            form['ctl00$MainContent$ChkDiffMailAddr'].checked = 'checked'
            form['ctl00$MainContent$ChkDiffMailAddr'].value = 'on'

            # remove the disabled attr on the relevant fields
            del self.browser.select('input[name="ctl00$MainContent$txtDiffStNamePO"]')[0]['disabled']
            del self.browser.select('input[name="ctl00$MainContent$txtDiffUnitApt"]')[0]['disabled']
            del self.browser.select('input[name="ctl00$MainContent$txtDiffCityTownCounty"]')[0]['disabled']
            del self.browser.select('input[name="ctl00$MainContent$txtDiffZip"]')[0]['disabled']
            del self.browser.select('select[name="ctl00$MainContent$ddlDiffStateTerr"]')[0]['disabled']

            # parse mailing address components
            mailing_address = get_address_from_freeform(user['separate_mailing_address'])
            mailing_components = mailing_address['components']

            # update fields with mailing address data
            form['ctl00$MainContent$txtDiffStNamePO'].value = get_street_address_from_components(mailing_components)
            if mailing_components.get('secondary_number'):
                form['ctl00$MainContent$txtDiffUnitApt'].value = get_address_unit_from_components(mailing_components)
            form['ctl00$MainContent$txtDiffCityTownCounty'].value = mailing_components['city_name']
            form['ctl00$MainContent$txtDiffZip'].value = mailing_components['zipcode']
            form['ctl00$MainContent$ddlDiffStateTerr'].value = mailing_components['state_abbreviation']

        # former name
        if user.get('has_previous_name'):
            prev_first, prev_last = split_name(user.get('previous_name'))

            del self.browser.select('input[name="ctl00$MainContent$txtFirstNameFormer"]')[0]['disabled']
            del self.browser.select('input[name="ctl00$MainContent$txtLastNameFormer"]')[0]['disabled']

            form['ctl00$MainContent$txtFirstNameFormer'] = prev_first
            form['ctl00$MainContent$txtLastNameFormer'] = prev_last

        # address where you were last registered to vote
        if user.get('has_previous_address'):
            form['ctl00$MainContent$ChkPrevRegAddr'].checked = 'checked'
            form['ctl00$MainContent$ChkPrevRegAddr'].value = 'on'

            # remove the disabled attr on the relevant fields
            del self.browser.select('input[name="ctl00$MainContent$TxtPrevRegStAddr"]')[0]['disabled']
            del self.browser.select('input[name="ctl00$MainContent$TxtPrevRegUnitApt"]')[0]['disabled']
            del self.browser.select('input[name="ctl00$MainContent$TxtPrevRegCityTownCounty"]')[0]['disabled']
            del self.browser.select('input[name="ctl00$MainContent$TxtPrevRegZip"]')[0]['disabled']
            del self.browser.select('select[name="ctl00$MainContent$ddlPrevRegStateTerr"]')[0]['disabled']

            # update fields with previous address data
            form['ctl00$MainContent$TxtPrevRegStAddr'] = user.get('previous_address', '')
            form['ctl00$MainContent$TxtPrevRegUnitApt'] = user.get('previous_address_unit', '')
            form['ctl00$MainContent$TxtPrevRegCityTownCounty'] = user.get('previous_city', '')
            form['ctl00$MainContent$TxtPrevRegZip'] = user.get('previous_zip', '')
            form['ctl00$MainContent$ddlPrevRegStateTerr'] = user.get('previous_state', '')

        self.browser.submit_form(form)

    def review(self, user, form):

        # I hereby swear (affirm) that I am the person named above, that the
        # above information is true, that I AM A CITIZEN OF THE UNITED STATES,
        # that I am not a person under guardianship which prohibits my
        # registering to vote, that I am not temporarily or permanantly
        # disqualified by law from voting because of corrupt practices in
        # respect to elections, that I am not currently incarcerated for a
        # felony conviction, and that I consider this residence to be my home.

        if user['us_citizen'] and user['legal_resident'] \
            and not (user['disqualified'] or user['disenfranchised']):

            form['ctl00$MainContent$ChkIsSwear'].checked = 'checked'
            form['ctl00$MainContent$ChkIsSwear'].value = 'on'

        elif not user['us_citizen']:
            self.add_error("You must be a U.S. Citizen.", field='us_citizen')

        elif not user['not_a_felon']:
            self.add_error("You must not be a felon.", field='not_a_felon')

        elif not user['legal_resident']:
            self.add_error("You must be a Massachusetts resident.", field='legal_resident')

        elif user['disenfranchised']:
            self.add_error("You may not register to vote if you are currently imprisoned or on parole for the conviction of a felony.", field='disenfranchised')

        elif user['disqualified']:
            self.add_error("You must not be legally disqualified to vote, or under legal guardianship which prohibits your registering. ", field='disqualified')

        self.browser.submit_form(form, submit=form['ctl00$MainContent$btnOnlineSubmitRev'])
