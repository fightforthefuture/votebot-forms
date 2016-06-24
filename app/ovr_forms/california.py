from base_ovr_form import BaseOVRForm


class California(BaseOVRForm):
    def __init__(self):
        super(California, self).__init__('https://covr.sos.ca.gov/?language=en-US')
