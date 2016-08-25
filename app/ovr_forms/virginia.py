from base_ovr_form import BaseOVRForm, OVRError
from form_utils import split_date, ValidationError
import sys, traceback
from robobrowser import RoboBrowser


class Virginia(BaseOVRForm):

    def __init__(self):
        super(Virginia, self).__init__('https://vote.elections.virginia.gov/VoterInformation')
        self.add_required_fields(['ssn_last_4', 'lawful_affirmation', 'county'])

    def submit(self, user, error_callback_url = None):

        self.error_callback_url = error_callback_url

        try:
            self.access_voter_record(user)
            # todo: get some VA voter registration data

            # also, don't break the law:
            # "I certify and affirm that the information provided
            # to access my voter registration is my own. I understand
            # that it is unlawful to access the record of any other
            # voter, punishable as computer fraud under Va. Code 18.2.152.3.*"
        except ValidationError, e:
            raise OVRError(self, message=e.message, payload=e.payload, error_callback_url=self.error_callback_url)

        except Exception, e:
            ex_type, ex, tb = sys.exc_info()
            raise OVRError(self, message="%s %s" % (ex_type, ex), payload=traceback.format_tb(tb), error_callback_url=self.error_callback_url)


    def access_voter_record(self, user):
        voter_record_form = self.browser.get_form()
        voter_record_form['FirstName'].value = user['first_name']
        voter_record_form['LastName'].value = user['last_name']

        (year, month, day) = split_date(user['date_of_birth'])
        voter_record_form['DateOfBirth'].value = '/'.join([month, day, year])

        # some BeautifulSoup / RoboBrowser jiu-jitsu
        # find the locality name (from elsewhere on virgnia.gov), see get_locality
        # and find the <option> tag which has that locality's name
        # as it's text / inner HTML, THEN set the <select> to have it's `value`
        # "a-very nice!"
        locality = self.get_locality(user)
        try:
            voter_record_form['LocalityUid'].value = self.browser.find_all('option', string=locality)[0]['value']
        except IndexError:
            # try falling back to "[locality] COUNTY"
            # this is a hack, but JAMES CITY was the first hit I found in testing
            # however, "JAMES CITY" wasn't listed. BUT, "JAMES CITY COUNTY" was, so...
            voter_record_form['LocalityUid'].value = self.browser.find_all('option', string="%s COUNTY" % locality)[0]['value']

        voter_record_form['SocialSecurityNumber'].value = user['ssn_last_4']
        voter_record_form['LawfulAffirmation'].checked = user['lawful_affirmation']

        # I'm gonna not do this yet, for legal reasons
        # self.browser.submit_form(voter_record_form)

    def get_locality(self, user):
        locality_browser = RoboBrowser()
        locality_browser.open('http://www.tax.virginia.gov/fips')
        locality_form = locality_browser.get_form(id="build-fips-form")
        locality_form['street1'] = user['address']
        locality_form['city'] = user['city']
        locality_form['zipcode'] = user['zip']
        # two 'op' buttons, submit & reset. thankfully submit is first.
        locality_browser.submit_form(locality_form, submit=locality_form['op'])
        return locality_browser.select('dl dd')[1].text.strip().upper()
        
