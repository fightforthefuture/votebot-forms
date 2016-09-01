from base_ovr_form import BaseOVRForm, OVRError
from form_utils import ValidationError
import sys, traceback

class DummyForm(BaseOVRForm):

    def __init__(self):
        super(DummyForm, self).__init__('https://www.hellovote.org')

    def submit(self, user, error_callback_url = None):

        self.error_callback_url = error_callback_url

        raise OVRError(self, message="Always fail", payload=self.browser.parsed, error_callback_url=self.error_callback_url)
        