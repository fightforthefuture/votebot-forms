from base_ovr_form import BaseOVRForm, OVRError
from form_utils import ValidationError, clean_browser_response, split_date, options_dict
import sys, traceback


class Hawaii(BaseOVRForm):

    def __init__(self):
        super(Hawaii, self).__init__('https://olvr.hawaii.gov/register.aspx')
        self.add_required_fields(['will_be_18', 'legal_resident', 'state_id_number', 'ssn'])
        self.success_string = 'TBD'

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
            forms = [
                self.identification,
            ]

            for handler in forms:
                handler(user)
                errors = self.parse_errors()
                if errors:
                    raise ValidationError(message='field_errors', payload=errors)

            success_page = clean_browser_response(self.browser)
            if self.success_string in success_page:
                return {'status': 'success'}
            else:
                raise ValidationError(message='no_success_string')

        except ValidationError, e:
            raise OVRError(self, message=e.message, payload=e.payload, error_callback_url=self.error_callback_url)

        except Exception, e:
            ex_type, ex, tb = sys.exc_info()
            raise OVRError(self, message="%s %s" % (ex_type, ex), payload=traceback.format_tb(tb), error_callback_url=self.error_callback_url)

    def identification(self, user):
        form = self.browser.get_form()

        form['ctl00$ContentPlaceHolder1$txtStep2FirstName'].value = user['first_name'].upper()
        form['ctl00$ContentPlaceHolder1$txtStep2LastName'].value = user['last_name'].upper()

        (year, month, day) = split_date(user['date_of_birth'])
        form['ctl00$ContentPlaceHolder1$rmtxtStep2DOB'].value = '/'.join([month, day, year])
        form['ctl00$ContentPlaceHolder1$ddlStep2Gender'].value = user['gender'].capitalize()

        form['ctl00$ContentPlaceHolder1$txtStep2DLID'].value = user['state_id_number']
        form['ctl00$ContentPlaceHolder1$rmtxtStep2SSN'].value = user['ssn']

        self.browser.submit_form(form, submit=form['ctl00$ContentPlaceHolder1$btnNext_2_19'])
