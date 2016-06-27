from base_ovr_form import BaseOVRForm


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
        drivers_license_form['ctl00$MainContent$rblDriversLicense'].value = 'Yes' if user['id_number'] else 'No'
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
        illinois_identification_form['ctl00$MainContent$tbILDLIDNumber'] = user['id_number'][0:3]
        illinois_identification_form['ctl00$MainContent$tbILDLIDNumber2'] = user['id_number'][4:7]
        illinois_identification_form['ctl00$MainContent$tbILDLIDNumber3'] = user['id_number'][8:11]

        try:
            year, month, day = user['date_of_birth'].split('-')

            # there's a Y2k bug lurking here for 2020...
            # todo: centralize / standardize how to handle and submit dates
            if len(year) == 2:
                year = '19%s' % year

            illinois_identification_form['ctl00$MainContent$tbDOB'].value = '-'.join([month.zfill(2), day.zfill(2), year])
        except:
            raise OVRError('date_of_birth must be in YYYY-MM-DD format')


        # similar to above but for driver's license issue date.
        try:
            year, month, day = user['id_issue_date'].split('-')

            # there's a Y2k bug lurking here for 2020...
            # todo: centralize / standardize how to handle and submit dates
            if len(year) == 2:
                year = '19%s' % year

            illinois_identification_form['ctl00$MainContent$tbIDIssuedDate'].value = '-'.join([month.zfill(2), day.zfill(2), year])
        except:
            raise OVRError('id_issue_date must be in YYYY-MM-DD format')

        self.browser.submit_form(illinois_identification_form, submit=illinois_identification_form['ctl00$MainContent$btnNext'])

        
