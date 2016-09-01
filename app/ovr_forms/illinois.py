from base_ovr_form import BaseOVRForm, OVRError
from form_utils import split_date, ValidationError, get_address_components, options_dict, get_address_from_freeform, bool_to_string
import sys, traceback

class Illinois(BaseOVRForm):

    def __init__(self):
        super(Illinois, self).__init__('https://ova.elections.il.gov/Step0.aspx')
        self.add_required_fields(['will_be_18', 'state_id_issue_date', 'ssn_last4',
            'county', 'gender', 'has_previous_name',
            'has_previous_address'])

    def submit(self, user, error_callback_url):

        self.error_callback_url = error_callback_url

        try:
            self.drivers_license(user)
            self.citizenship(user)
            self.age_verification(user)
            self.application_type(user)
            self.illinois_identification(user)
            self.illinois_name(user)
            self.illinois_address(user)
            self.illinois_personal_info(user)
            self.illinois_email(user)
            self.illinois_election_authority(user)
            self.illinois_mailing_address(user)
            self.illinois_different_name(user)
            self.illinois_different_address(user)
            self.illinois_assisting(user)
            self.illinois_summary(user)

            return {'status': 'failure', 'note': 'JL NOTE ~ Not sure what to do...'}

        except ValidationError, e:
            raise OVRError(self, message=e.message, payload=e.payload, error_callback_url=self.error_callback_url)

        except Exception, e:
            ex_type, ex, tb = sys.exc_info()
            raise OVRError(self, message="%s %s" % (ex_type, ex), payload=traceback.format_tb(tb), error_callback_url=self.error_callback_url)

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

    def illinois_name(self, user):
        self.browser.open('https://ova.elections.il.gov/Step4b.aspx')
        illinois_name_form = self.browser.get_form()

        illinois_name_form['ctl00$MainContent$tbFirstName'] = user['first_name']
        illinois_name_form['ctl00$MainContent$tbLastName'] = user['last_name']

        self.browser.submit_form(illinois_name_form, submit=illinois_name_form['ctl00$MainContent$btnNext'])

    def illinois_address(self, user):
        self.browser.open('https://ova.elections.il.gov/Step5.aspx')
        frm = self.browser.get_form()

        address_components = get_address_components(user['address'], user['city'], user['state'], user['zip'])

        frm['ctl00$MainContent$tbResidentStreetNumber'].value = address_components['primary_number']

        if 'street_predirection' in address_components:
            frm['ctl00$MainContent$ddlResidentStreetDirection'].value = options_dict(frm['ctl00$MainContent$ddlResidentStreetDirection'])[address_components['street_predirection'].upper()]

        frm['ctl00$MainContent$tbResidentStreetName'].value = address_components['street_name']
        frm['ctl00$MainContent$ddlResidentStreetType'].value = options_dict(frm['ctl00$MainContent$ddlResidentStreetType'])[address_components['street_suffix'].upper()]

        if 'street_postdirection' in address_components:
            frm['ctl00$MainContent$ddlResidentPostDirection'].value = options_dict(frm['ctl00$MainContent$ddlResidentPostDirection'])[address_components['street_postdirection'].upper()]

        if user.get('apartment') and not user.get('apartment').lower == "none":
            frm['ctl00$MainContent$tbResidentAptRmSuite'].value = user.get('apartment')

            if 'secondary_designator' in address_components:
                try:
                    frm['ctl00$MainContent$ddlResidentAptRmBoxSuite'].value = options_dict(frm['ctl00$MainContent$ddlResidentAptRmBoxSuite'])[address_components['secondary_designator']]
                except:
                    pass

        frm['ctl00$MainContent$tbResidentCity'].value = address_components['city_name']
        frm['ctl00$MainContent$tbResidentZip'].value = address_components['zipcode']

        self.browser.submit_form(frm, submit=frm['ctl00$MainContent$btnNext'])

    def illinois_personal_info(self, user):
        self.browser.open('https://ova.elections.il.gov/Step6.aspx')
        frm = self.browser.get_form()

        frm['ctl00$MainContent$tbSSN'].value = user['ssn_last4']
        frm['ctl00$MainContent$rblSex'].value = 'F' if 'f' in user['gender'].lower() else 'M'

        self.browser.submit_form(frm, submit=frm['ctl00$MainContent$btnNext'])

    def illinois_email(self, user):
        self.browser.open('https://ova.elections.il.gov/Step7.aspx')
        frm = self.browser.get_form()

        frm['ctl00$MainContent$tbEmail'].value = user['email']
        frm['ctl00$MainContent$tbVerifyEmail'].value = user['email']

        self.browser.submit_form(frm, submit=frm['ctl00$MainContent$btnNext'])        

    def illinois_election_authority(self, user):
        self.browser.open('https://ova.elections.il.gov/Step8.aspx')
        frm = self.browser.get_form()

        election_authority = self.determine_election_authority(user["city"], user["county"])
        frm['ctl00$MainContent$ddlElectionAuthoritySelect'].value = options_dict(frm['ctl00$MainContent$ddlElectionAuthoritySelect'])[election_authority]

        self.browser.submit_form(frm, submit=frm['ctl00$MainContent$btnNext'])  

    def illinois_mailing_address(self, user):
        self.browser.open('https://ova.elections.il.gov/Step9.aspx')
        frm = self.browser.get_form()

        self.browser.submit_form(frm, submit=frm['ctl00$MainContent$btnNext'])

    def illinois_different_name(self, user):
        self.browser.open('https://ova.elections.il.gov/Step10.aspx')
        frm = self.browser.get_form()

        if user["has_previous_name"]:
            previous_name_space_count = user["previous_name"].count(' ')
            previous_name_split = user["previous_name"].split(' ', 2)

            if previous_name_space_count == 1:
                first_name = previous_name_split[0]
                middle_name = ''
                last_name = previous_name_split[1]
            else:
                first_name = previous_name_split[0]
                middle_name = previous_name_split[1]
                last_name = previous_name_split[2]

            frm["ctl00$MainContent$rblFormerName"].value = "Yes"
            frm["ctl00$MainContent$tbFormerFirstName"].value = first_name
            frm["ctl00$MainContent$tbFormerMiddleName"].value = middle_name
            frm["ctl00$MainContent$tbFormerLastName"].value = last_name

        else:
            frm["ctl00$MainContent$rblFormerName"].value = "No"

        self.browser.submit_form(frm, submit=frm['ctl00$MainContent$btnNext'])

    def illinois_different_address(self, user):
        self.browser.open('https://ova.elections.il.gov/Step10b.aspx')
        frm = self.browser.get_form()

        if user["has_previous_address"]:
            address = get_address_from_freeform(user['previous_address'])
            address_components = address["components"]

            frm['ctl00$MainContent$tbFormerStreetNumber'].value = address_components['primary_number']

            if 'street_predirection' in address_components:
                frm['ctl00$MainContent$ddlFormerStreetDirection'].value = options_dict(frm['ctl00$MainContent$ddlFormerStreetDirection'])[address_components['street_predirection'].upper()]

            frm['ctl00$MainContent$tbFormerStreetName'].value = address_components['street_name']
            frm['ctl00$MainContent$ddlFormerStreetType'].value = options_dict(frm['ctl00$MainContent$ddlFormerStreetType'])[address_components['street_suffix'].upper()]

            if 'street_postdirection' in address_components:
                frm['ctl00$MainContent$ddlFormerPostDirection'].value = options_dict(frm['ctl00$MainContent$ddlFormerPostDirection'])[address_components['street_postdirection'].upper()]

            frm['ctl00$MainContent$tbFormerCity'].value = address_components['city_name']
            frm['ctl00$MainContent$tbFormerZip'].value = address_components['zipcode']

            election_authority = self.determine_election_authority(address_components['city_name'], address['metadata']['county_name'])
            frm['ctl00$MainContent$ddlCountySelect'].value = options_dict(frm['ctl00$MainContent$ddlCountySelect'])[election_authority]

        else:
            frm["ctl00$MainContent$rblFormerAddress"].value = "No"

        self.browser.submit_form(frm, submit=frm['ctl00$MainContent$btnNext'])

    def illinois_assisting(self, user):
        self.browser.open('https://ova.elections.il.gov/Step11.aspx')
        frm = self.browser.get_form()

        frm["ctl00$MainContent$rblAssisted"].value = "Personal"

        self.browser.submit_form(frm, submit=frm['ctl00$MainContent$btnNext'])

    def illinois_summary(self, user):
        self.browser.open('https://ova.elections.il.gov/Step12.aspx')
        frm = self.browser.get_form()

        user_is_eligible = user['us_citizen'] and user['will_be_18']

        frm['ctl00$MainContent$cbLegalConfirmation'].value = bool_to_string(user_is_eligible)
        frm['ctl00$MainContent$cbLegalConfirmation'].checked = 'checked'

        self.browser.submit_form(frm, submit=frm['ctl00$MainContent$btnFinish'])

    def determine_election_authority(self, city, county):

        if city == 'Chicago':
            return 'CITY OF CHICAGO'
        elif city == 'Aurora':
            return 'CITY OF AURORA'
        elif city == 'Galesburg':
            return 'CITY OF GALESBURG'
        elif city == 'Bloomington':
            return 'CITY OF BLOOMINGTON'
        elif city == 'East Saint Louis':
            return 'CITY OF EAST ST.LOUIS'
        elif city == 'Danville':
            return 'CITY OF DANVILLE'
        elif city == 'Rockford':
            return 'CITY OF ROCKFORD'
        elif county == 'Cook':
            return 'COOK - SUBURBS'
        else:
            return county.upper()



        
