from app.ovr_forms.base_ovr_form import BaseOVRForm, OVRError
from app.ovr_forms.form_utils import ValidationError, split_date

import storage

from fdfgen import forge_fdf
import subprocess
import json
import os, sys, traceback

PDFTK_BIN = os.environ.get('PDFTK_BIN', 'pdftk')
SOS_ADDRESS = json.load(open('app/pdf_forms/sos_address.json', 'r'))

class NVRA(BaseOVRForm):
    def __init__(self):
        super(NVRA, self).__init__()
        self.form_template = os.path.abspath('app/pdf_forms/templates/coversheet+form.pdf')
        self.add_required_fields(['us_citizen', 'will_be_18', 'political_party', 'state_id_number'])

    def match_fields(self, user):
        form = {}
        if user['us_citizen']:
            form['us_citizen_yes'] = True
        else:
            self.add_error('You must be a US citizen to register to vote.', field='us_citizen')
            return False

        if user['will_be_18']:
            form['will_be_18_yes'] = True
        else:
            self.add_error('You must be 18 by Election Day in order to register to vote.', field='will_be_18')
            return False

        if user.get('gender') == 'M':
            form['title_mr'] = True
        elif user.get('gender') == 'F':
            form['title_ms'] = True
        # TODO handle Miss, Mrs?
            
        form['first_name'] = user.get('first_name')
        # form['middle_name'] = user.get('middle_name')
        form['last_name'] = user.get('last_name')
        form['home_address'] = user.get('address')
        form['home_apt'] = user.get('address_unit', '')
        form['home_city'] = user.get('city')
        form['home_state'] = user.get('state')
        form['home_zip'] = user.get('zip')
        (year, month, day) = split_date(user.get('date_of_birth'))
        form['date_of_birth'] = ' / '.join((month, day, year))
        form['phone_number'] = user.get('phone', '')
        form['choice_of_party'] = user.get('political_party', '')
        form['id_number'] = user.get('state_id_number', '')
        form['race_ethnic_group'] = user.get('ethnicity', '')
        
        # TODO get local election offical address from Google Civic or US OVF
        # until Google Civic updates, use statewide address
        sos_address = SOS_ADDRESS.get(user.get('state'))
        if sos_address:
            form['mailto'] = '\n'.join(sos_address)
            form['mailto_line_1'] = sos_address[0]
            if len(sos_address) > 1:
                form['mailto_line_2'] = sos_address[1]
            if len(sos_address) > 2:
                form['mailto_line_3'] = sos_address[2]
            if len(sos_address) > 3:
                form['mailto_line_4'] = sos_address[3]
            if len(sos_address) > 4:
                form['mailto_line_5'] = sos_address[4]

        form['registration_deadline'] = user.get('registration_deadline', 'Put the form in the mail at least 15 days before election day')

        return form

    def generate_pdf(self, form_data):
        # generate fdf data
        fdf_stream = forge_fdf(fdf_data_strings=form_data, checkbox_checked_name="On")

        # fill out form template
        pdftk_fill = [PDFTK_BIN,
                     self.form_template, 'fill_form', '-',
                     'output', '-', 'flatten']
        process = subprocess.Popen(' '.join(pdftk_fill), shell=True,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        (stdout, stderr) = process.communicate(input=fdf_stream)
        return stdout

    def submit(self, user, error_callback_url=None):
        self.error_callback_url = error_callback_url

        try:
            form_data = self.match_fields(user)
            pdf_file = self.generate_pdf(form_data)
            if pdf_file:
                self.pdf_url = storage.upload_to_s3(pdf_file, 'print/%s.pdf' % self.uid)
                return {'status': 'success', 'pdf_url': self.pdf_url}
            else:
                return {'status': 'error', 'message': 'unable to generate NVRA pdf'}

        except ValidationError, e:
            raise OVRError(self, message=e.message, payload=e.payload, error_callback_url=self.error_callback_url)

        except Exception, e:
            ex_type, ex, tb = sys.exc_info()
            raise OVRError(self, message="%s %s" % (ex_type, ex), payload=traceback.format_tb(tb), error_callback_url=self.error_callback_url)
