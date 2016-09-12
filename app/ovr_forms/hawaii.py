from base_ovr_form import BaseOVRForm, OVRError
from form_utils import ValidationError, clean_browser_response
import sys, traceback


class Hawaii(BaseOVRForm):

    def __init__(self):
        super(Hawaii, self).__init__('https://olvr.hawaii.gov/register.aspx')
        self.add_required_fields(['will_be_18', 'legal_resident', 'state_id_number', 'ssn'])
        self.success_string = 'TBD'

    def submit(self, user, error_callback_url=None):

        self.error_callback_url = error_callback_url

        try:
            forms = [

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
