from base_ovr_form import BaseOVRForm


class Georgia(BaseOVRForm):
    def __init__(self):
        super(Georgia, self).__init__('https://registertovote.sos.ga.gov/GAOLVR/welcometoga.do')
        # todo: you can check if you are registered at https://www.mvp.sos.ga.gov/MVP/mvp.do

    def welcome(self):
        ovr_welcome_form = self.browser.get_form()
        # select OVR
        self.browser.submit_form(ovr_welcome_form, submit=ovr_welcome_form['ddsIdButton'])
        return ovr_welcome_form

    def minimum_requirements(self):
        min_req_form = self.browser.get_form()
        min_req_form['citizenVer'].checked = True
        min_req_form['ageVer'].checked = True
        min_req_form['stateVer'].checked = True
        min_req_form['felonyVer'].checked = True
        min_req_form['mentally'].checked = True
        # every GA form has a "back" button which also does a submit, so we have to specify
        self.browser.submit_form(min_req_form, submit=min_req_form['beginReg'])
        return min_req_form

    def get_county(self, user):
        # this takes place in a modal on the site.
        county_req = self.browser.session.get('https://registertovote.sos.ga.gov/GAOLVR/getCounties.do?zipcode=%s' % user['home_zip'])
        county_json = county_req.json()
        return county_json[0]['key']

    def registration(self, user):
        registration_form = self.browser.get_form()
        # new voter
        registration_form['changeType'] = 'NV'
        registration_form['county'] = self.get_county(user)
        
        registration_form['lastName'] = user['last_name']
        registration_form['firstName'] = user['first_name']

        try:
            year, month, day = user['date_of_birth'].split('-')

            # there's a Y2k bug lurking here for 2020...
            # todo: centralize / standardize how to handle and submit dates
            if len(year) == 2:
                year = '19%s' % year

            registration_form['dobDate'] = '/'.join([month.zfill(2), day.zfill(2), year])
        except:
            raise OVRError('date must be in YYYY-MM-DD format')

        registration_form['ddsId'] = user['id_number']
        
        self.browser.submit_form(registration_form, submit=registration_form['next'])
        return registration_form

    def submit(self, user):
        self.welcome()
        self.minimum_requirements()
        self.registration(user)
        # todo: I need a valid GA driver's license.