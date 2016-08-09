from base_ovr_form import BaseOVRForm
from form_utils import split_date


class Illinois(BaseOVRForm):

    def __init__(self):
        super(Illinois, self).__init__('https://ova.elections.il.gov/Step0.aspx')

    def submit(self, user):
        self.drivers_license(user)
        self.citizenship(user)
        self.age_verification(user)
        self.application_type(user)
        self.illinois_identification(user)

    def drivers_license(self, user):
        drivers_license_form = self.browser.get_form()
        drivers_license_form['ctl00$MainContent$rblDriversLicense'].value = 'Yes' if user['state_id_number'] else 'No'
        self.browser.submit_form(drivers_license_form, submit=drivers_license_form['ctl00$MainContent$btnNext'])

    def citizenship(self, user):
        # IL's site does this "interesting" ASP.net trick where
        # it submits the data as a POST using JS, then GETs the next
        # page. probably some kind of cached-301-defeating technique
        # but we will press on with the POSTs and the subsequent GETs
        self.browser.open('https://ova.elections.il.gov/Step1.aspx')
        citizenship_form = self.browser.get_form()
        citizenship_form['ctl00$MainContent$rblCitizen'].value = 'Yes' if user['us_citizen'] else 'No'
        self.browser.submit_form(citizenship_form, submit=citizenship_form['ctl00$MainContent$btnNext'])

    def age_verification(self, user):
        self.browser.open('https://ova.elections.il.gov/Step2.aspx')
        age_verification_form = self.browser.get_form()
        age_verification_form['ctl00$MainContent$rblAgeVerification'].value = 'Yes' if user['will_be_18'] else 'No'
        self.browser.submit_form(age_verification_form, submit=age_verification_form['ctl00$MainContent$btnNext'])

    def application_type(self, user):
        self.browser.open('https://ova.elections.il.gov/Step3.aspx')
        application_type_form = self.browser.get_form()
        application_type_form['ctl00$MainContent$rblApplicationType'].value = 'R'
        self.browser.submit_form(application_type_form, submit=application_type_form['ctl00$MainContent$btnNext'])

    def illinois_identification(self, user):
        self.browser.open('https://ova.elections.il.gov/Step4.aspx')
        illinois_identification_form = self.browser.get_form()
        illinois_identification_form['ctl00$MainContent$tbILDLIDNumber'] = user['state_id_number'][0:3]
        illinois_identification_form['ctl00$MainContent$tbILDLIDNumber2'] = user['state_id_number'][4:7]
        illinois_identification_form['ctl00$MainContent$tbILDLIDNumber3'] = user['state_id_number'][8:11]

        (dob_year, dob_month, dob_day) = split_date(user['date_of_birth'])
        illinois_identification_form['ctl00$MainContent$tbDOB'].value = '-'.join([dob_month, dob_day, dob_year])

        (id_year, id_month, id_day) = split_date(user['date_of_birth'])   
        illinois_identification_form['ctl00$MainContent$tbIDIssuedDate'].value = '-'.join([id_month, id_day, id_year])
        
        self.browser.submit_form(illinois_identification_form, submit=illinois_identification_form['ctl00$MainContent$btnNext'])

        
