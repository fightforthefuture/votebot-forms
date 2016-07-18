from base_ovr_form import BaseOVRForm
from form_utils import get_address_components, options_dict, split_date


class Massachusetts(BaseOVRForm):

    def __init__(self):
        super(Massachusetts, self).__init__('https://www.sec.state.ma.us/OVR/Pages/MinRequirements.aspx?RMVId=True')
        self.add_required_fields(['will_be_18', 'legal_resident', 'consent_use_signature', 'political_party'])

    def submit(self, user):
        self.minimum_requirements(user)
        self.rmv_identification(user)
        self.complete_form(user)
        self.review(user)

    def minimum_requirements(self, user):
        # this doesn't actually do a form submit, but if it did, it would look like ...
        # min_req_form = self.browser.get_form(id="form1")
        # min_req_form['ctl00$MainContent$ChkCitizen'].checked = user['us_citizen']
        # min_req_form['ctl00$MainContent$ChkAge'].checked = user['will_be_18']
        # min_req_form['ctl00$MainContent$ChkResident'].checked = user['legal_resident']
        # self.browser.submit_form(min_req_form, submit=min_req_form['ctl00$MainContent$BtnBeginOVR'])
        
        # woe is me.
        pass

    def rmv_identification(self, user):
        self.browser.open('https://www.sec.state.ma.us/OVR/Pages/FormAndReview.aspx?RMVId=True')
        rmv_id_form = self.browser.get_form(id="form1")
        rmv_id_form['ctl00$MainContent$TxtFirstName'].value = user['first_name']
        rmv_id_form['ctl00$MainContent$TxtLastName'].value = user['last_name']

        (year, month, day) = split_date(user['date_of_birth'])
        rmv_id_form['ctl00$MainContent$TxtDoB'].value = '/'.join([month, day, year])

        rmv_id_form['ctl00$MainContent$TxtRMVID'].value = user['id_number']
        
        rmv_id_form['ctl00$MainContent$ChkConsent'].checked = 'checked' if user['consent_use_signature'] else ''
        rmv_id_form['ctl00$MainContent$ChkConsent'].value = 'on' if user['consent_use_signature'] else 'off'

        self.browser.submit_form(rmv_id_form, submit=rmv_id_form['ctl00$MainContent$BtnValidate'])

    def complete_form(self, user):

        # crucial - un-disable the party list
        del self.browser.select('select[name="ctl00$MainContent$ddlPartyList"]')[0]['disabled']

        form = self.browser.get_form(id='form1')
        address_components = get_address_components(user['home_address'], user['home_city'], user['state'], user['home_zip'])

        form['ctl00$MainContent$txtStNum'].value = address_components['primary_number']
        form['ctl00$MainContent$txStNameSuffix'].value = address_components['street_name']

        # todo: these two seem fraught for IndexErrors
        form['ctl00$MainContent$ddlStreetSuffix'].value = options_dict(form['ctl00$MainContent$ddlStreetSuffix'])[address_components['street_suffix'].upper()]
        form['ctl00$MainContent$ddlCityTown'].value = options_dict(form['ctl00$MainContent$ddlCityTown'])[user['home_city']]

        form['ctl00$MainContent$txtZip'].value = user['home_zip']

        # todo: more delicateness needed here.
        form['ctl00$MainContent$PartyEnrolled'].value ='rdoBtnParty' if user['political_party'] else ''
        form['ctl00$MainContent$ddlPartyList'].value = options_dict(form['ctl00$MainContent$ddlPartyList'])[user['political_party']]

        # possible todos, all optional:
        # former name
        # separate mailing address
        # phone number
        # address where you were last registered to vote.

        self.browser.submit_form(form)

    def review(self, user):
        review_form = self.browser.get_form(id='form1')
        review_form['ctl00$MainContent$ChkIsSwear'].checked = 'checked'
        review_form['ctl00$MainContent$ChkIsSwear'].value = 'on'

        # untested
        # self.browser.submit_form(review_form)