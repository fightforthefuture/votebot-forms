from base_ovr_form import BaseOVRForm
from form_utils import split_date


class Massachusetts(BaseOVRForm):

    def __init__(self):
        super(Massachusetts, self).__init__('https://www.sec.state.ma.us/OVR/Pages/MinRequirements.aspx?RMVId=True')
        self.required_fields.extend(['will_be_18', 'legal_resident', 'consent_get_signature_from_rmv'])

    def submit(self, user):
        self.minimum_requirements(user)
        self.rmv_identification(user)
        # todo: get MA driver's license info.

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
        rmv_id_form['ctl00$MainContent$ChkConsent'].checked = user['consent_get_signature_from_rmv']

        self.browser.submit_form(rmv_id_form, submit=rmv_id_form['ctl00$MainContent$BtnValidate'])


