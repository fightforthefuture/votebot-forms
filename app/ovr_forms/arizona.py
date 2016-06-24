from base_ovr_form import BaseOVRForm


class Arizona(BaseOVRForm):
    def __init__(self):
        super(Arizona, self).__init__('https://servicearizona.com/webapp/evoter/register?execution=e1s2')
