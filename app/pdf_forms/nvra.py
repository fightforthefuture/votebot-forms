from app.ovr_forms.base_ovr_form import BaseOVRForm, OVRError
from app.ovr_forms.form_utils import ValidationError, split_date

from fdfgen import forge_fdf
import subprocess
import tempfile
import json
import os, sys, traceback

PDFTK_BIN = os.environ.get('PDFTK_BIN', '/usr/local/bin/pdftk')


class NVRA(BaseOVRForm):
    def __init__(self):
        super(NVRA, self).__init__()
        self.coversheet = os.path.abspath('app/pdf_forms/templates/coversheet.pdf')
        self.form_template = os.path.abspath('app/pdf_forms/templates/eac-nvra.pdf')
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
        form['home_apt'] = user.get('apt')
        form['home_city'] = user.get('city')
        form['home_state'] = user.get('state')
        form['home_state'] = user.get('zip')
        (year, month, day) = split_date(user.get('date_of_birth'))
        form['date_of_birth'] = ' / '.join((month, day, year))
        form['phone_number'] = user.get('phone')
        form['political_party'] = user.get('political_party')
        form['id_number'] = user.get('state_id_number')
        form['race_ethnic_group'] = user.get('ethnicity')
        
        # TODO get local election offical address from Google Civic or US OVF
        # until Google Civic updates, use statewide address
        form['mailto_line_1'] = 'TEST ADDRESS'
        form['mailto_line_2'] = 'STATE OFFICE'
        form['mailto_line_3'] = 'CAPITOL CITY'
        form['mailto_line_4'] = 'ANY STATE'
        form['mailto_line_5'] = 'ANY STATE'

        return form

    def generate_pdf(self, user):
        # generate fdf data
        fdf_stream = forge_fdf(fdf_data_strings=user)

        # fill out form template
        pdftk_fill = [PDFTK_BIN,
                     self.form_template, 'fill_form', '-',
                     'output', '-', 'flatten']
        process = subprocess.Popen(' '.join(pdftk_fill), shell=True,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        (stdout, stderr) = process.communicate(input=fdf_stream)

        # join with coversheet
        pdftk_join = [PDFTK_BIN,
                     self.coversheet, '-', 'cat',
                     'output', '-']
        process = subprocess.Popen(' '.join(pdftk_join), shell=True,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        (stdout, stderr) = process.communicate(input=stdout)
        self.pdftk_output = "'%s'" % stdout
        return stdout

    def write_to_tmp(self, pdf_stream):
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.write(pdf_stream)
        tmp.close()
        return tmp.name

    def upload_to_s3(self, pdf_stream):
        pass
        # TODO upload to s3 via boto

    def submit(self, user, error_callback_url=None):
        self.error_callback_url = error_callback_url

        try:
            form_data = self.match_fields(user)
            pdf_file = self.generate_pdf(form_data)
            if pdf_file:
                pdf_url = self.write_to_tmp(pdf_file)
                return {'status': 'success', 'pdf_url': pdf_url}
            else:
                return {'status': 'error', 'message': 'unable to generate NVRA pdf'}

        except ValidationError, e:
            raise OVRError(self, message=e.message, payload=e.payload, error_callback_url=self.error_callback_url)

        except Exception, e:
            ex_type, ex, tb = sys.exc_info()
            raise OVRError(self, message="%s %s" % (ex_type, ex), payload=traceback.format_tb(tb), error_callback_url=self.error_callback_url)
