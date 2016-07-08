from base_ovr_form import BaseOVRForm
from form_utils import bool_to_string, split_date, options_dict


class Colorado(BaseOVRForm):
    def __init__(self):
        super(Colorado, self).__init__('https://www.sos.state.co.us/voter-classic/pages/pub/olvr/verifyNewVoter.xhtml')
        # self.required_fields.extend([])

    def submit(self, user):
        self.verify_identification(user)

    def verify_identification(self, user):
        verify_identification_form = self.browser.get_form(id='verifyNewVoterForm')

        verify_identification_form['verifyNewVoterForm:voterSearchLastId'].value = user['last_name']
        verify_identification_form['verifyNewVoterForm:voterSearchFirstId'].value = user['first_name']

        (year, month, day) = split_date(user['date_of_birth'])
        verify_identification_form['verifyNewVoterForm:voterDOB'].value = '/'.join(month, day, year)

        verify_identification_form['verifyNewVoterForm:driverId'].value = user['id_number']

        self.browser.submit_form(verify_identification_form, submit=verify_identification_form['verifyNewVoterForm:voterSearchButtonId'])