from app.ovr_forms.base_ovr_form import BaseOVRForm, OVRError
from app.ovr_forms.form_utils import ValidationError, split_date, split_name, parse_gender

import storage
import postage
import election_mail

from fdfgen import forge_fdf
import subprocess
import tempfile
import logging
import os, sys, traceback

log = logging.getLogger(__name__)

PDFTK_BIN = os.environ.get('PDFTK_BIN', 'pdftk')
GS_BIN = os.environ.get('GS_BIN', 'gs')


class NVRA(BaseOVRForm):
    def __init__(self, mail_deadline=None):
        super(NVRA, self).__init__()
        self.coversheet_email = os.path.abspath('app/pdf_forms/templates/coversheet-email.pdf')
        self.coversheet_email_nostamp = os.path.abspath('app/pdf_forms/templates/coversheet-email-nostamp.pdf')
        self.coversheet_letter = os.path.abspath('app/pdf_forms/templates/coversheet-letter.pdf')
        self.coversheet_letter_nostamp = os.path.abspath('app/pdf_forms/templates/coversheet-letter-nostamp.pdf')
        self.letter_template = os.path.abspath('app/pdf_forms/templates/letter.pdf')
        self.form_template = os.path.abspath('app/pdf_forms/templates/eac-nvra.pdf')
        self.add_required_fields(['us_citizen', 'will_be_18'])
        self.pdf_url = ''
        if mail_deadline:
            self.mail_deadline_text = mail_deadline
        else:
            self.mail_deadline_text = "The mailing deadline is soon"

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

        if user.get('gender'):
            try:
                gender_str = parse_gender(user.get('gender'))
                if gender_str is 'M':
                    form['title_mr'] = True
                elif gender_str is 'F':
                    form['title_ms'] = True
            except ValidationError:
                pass

        form['first_name'] = user.get('first_name')
        form['middle_name'] = user.get('middle_name', '')
        form['last_name'] = user.get('last_name')
        form['home_address'] = user.get('address')
        form['home_apt'] = user.get('address_unit', '')
        form['home_city'] = user.get('city')
        form['home_state'] = user.get('state')
        form['home_zip'] = user.get('zip')

        # previous address
        if user.get('has_previous_address'):
            form['change_address'] = user.get('previous_address', '')
            form['change_apt'] = user.get('previous_address_unit', '')
            form['change_city'] = user.get('previous_city', '')
            form['change_state'] = user.get('previous_state', '')
            form['change_zip'] = user.get('previous_zip', '')

        # previous name
        if user.get('has_previous_name'):
            prev_first, prev_middle, prev_last = split_name(user.get('previous_name', ''))
            form['change_first_name'] = prev_first
            form['change_middle_name'] = prev_middle
            form['change_last_name'] = prev_last

        # rest of form
        (year, month, day) = split_date(user.get('date_of_birth'))
        form['date_of_birth'] = ' / '.join((month, day, year))
        form['phone_number'] = user.get('phone', '')
        form['choice_of_party'] = user.get('political_party', '')
        form['id_number'] = user.get('state_id_number', '')
        form['race_ethnic_group'] = user.get('ethnicity', '')

        # state specific id requirements
        state = user.get('state')
        # these states require full SSN
        if state in ('AL', 'HI', 'KY', 'TN', 'NM', 'SC', 'VA'):
            form['id_number'] = user.get('ssn')
        # these states want full SSN as a backup to state ID
        if state in ('OH', ):
            if not form.get('id_number'):
                form['id_number'] = user.get('ssn')
        # these states require last 4 AND state ID
        if state in ('OK', 'MO'):
            form['id_number'] = "%s %s" % (user.get('ssn_last4'), user.get('state_id_number', ''))
        # these states want last 4 as a backup
        if state in ('AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'GA', 'FL', 'ID',
                     'IL', 'IN', 'IA', 'KS', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS',
                     'MT', 'NE', 'NV', 'NJ', 'NY', 'NC', 'OR', 'PA', 'RI', 'SD', 'TX',
                     'UT', 'VT', 'WA', 'WV', 'WI'):
            if not form.get('id_number'):
                form['id_number'] = user.get('ssn_last4')

        # if nothing entered yet, fallback to NONE
        if not form.get('id_number'):
            form['id_number'] = "NONE"

        # include mail deadline for letters
        form['mail_deadline'] = self.mail_deadline_text

        mailto_dict = election_mail.get_mailto_address(user)
        # format mailto values to correct address
        if mailto_dict:
            mailto_list = [mailto_dict['name'], mailto_dict['street1']]
            if 'street2' in mailto_dict:
                mailto_list.append(mailto_dict['street2'])
            mailto_list.append("%(city)s %(state)s %(zip)s" % mailto_dict)
            form['mailto'] = '\n'.join(mailto_list)

        form['return_address'] = '\n'.join([
            u"{first_name} {last_name}".format(**user),
            u"{address} {unit}".format(
                address=user.get('address'),
                unit=user.get('address_unit', '')  # default to avoid KeyError
            ),
            u"{city} {state} {zip}".format(**user)
        ])
        return form

    def run_subprocess(self, command, input_stream=None):
        if type(command) == list:
            command = ' '.join(command)

        log.debug(command)
        process = subprocess.Popen(command, shell=True,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        log.debug('start')
        if input_stream:
            log.debug(input_stream)
            (out, err) = process.communicate(input=input_stream)
        else:
            (out, err) = process.communicate()
        log.debug('done')

        if out:
            log.info(out)
        if err:
            log.error(err)

    def generate_pdf(self, form_data, to_address, include_postage=False, mail_letter=False):
        # generate fdf data
        fdf_stream = forge_fdf(fdf_data_strings=form_data, checkbox_checked_name="On")

        # fill out form template to tempfile
        filled_form_tmp = tempfile.NamedTemporaryFile()
        pdftk_fill = [PDFTK_BIN,
                     self.form_template, 'fill_form', '-',
                     'output', filled_form_tmp.name, 'flatten']
        self.run_subprocess(pdftk_fill, fdf_stream)

        coversheet_tmp = tempfile.NamedTemporaryFile()

        if include_postage:
            # try to buy a mailing label
            from_address = {
                "name": u"{first_name} {last_name}".format(**form_data),
                "street1": form_data.get('home_address'),
                "street2": form_data.get('home_apt'),
                "city": form_data.get('home_city'),
                "state": form_data.get('home_state'),
                "zip": form_data.get('home_zip'),
                "country": 'US',
            }
            mailing_label = postage.buy_mailing_label(to_address, from_address)
        else:
            mailing_label = False

        if mail_letter:
            if mailing_label:
                coversheet_template = self.coversheet_letter
            else:
                coversheet_template = self.coversheet_letter_nostamp
        else:
            if mailing_label:
                coversheet_template = self.coversheet_email
            else:
                coversheet_template = self.coversheet_email_nostamp

        if mailing_label:
            # write it to a tempfile, so we can adjust it to fit
            # don't delete automatically, because ghostscript needs a handle
            mailing_label_tmp = tempfile.NamedTemporaryFile(delete=False)
            mailing_label_tmp.write(mailing_label)
            mailing_label_tmp.close()

            if mail_letter:
                # rotate with pdftk
                mailing_label_rotate_tmp = tempfile.NamedTemporaryFile(delete=False)
                pdftk_mailing_label_rotate = [PDFTK_BIN,
                     mailing_label_tmp.name, 'rotate', '1-1south',
                     'output', mailing_label_rotate_tmp.name]
                self.run_subprocess(pdftk_mailing_label_rotate)
                stamp_offset = '[0 550]'  # offset vertically back up the page

                mailing_label_tmp = mailing_label_rotate_tmp
            else:
                stamp_offset = '[0 -450]'  # center page bottom

            # offset it with ghostscript
            # because pdftk can't adjust stamp location
            stamp_tmp = tempfile.NamedTemporaryFile()
            gs_offset = [GS_BIN, '-q', '-o', stamp_tmp.name,
                         '-sDEVICE=pdfwrite',
                         '-g6120x7920',  # dimensions in points * 10
                         '-c "<</PageOffset %s>> setpagedevice"' % stamp_offset,
                         '-f', mailing_label_tmp.name]
            self.run_subprocess(gs_offset)

            # delete mailing label file
            os.remove(mailing_label_tmp.name)

            # stamp it on the coversheet
            pdftk_stamp_coversheet = [PDFTK_BIN,
                 coversheet_template, 'stamp', stamp_tmp.name,
                 'output', coversheet_tmp.name]
            self.run_subprocess(pdftk_stamp_coversheet)

        else:
            # fill out coversheet with mailto field from fdf_stream
            pdftk_fill_coversheet = [PDFTK_BIN,
                 coversheet_template, 'fill_form', '-',
                 'output', coversheet_tmp.name, 'flatten']
            self.run_subprocess(pdftk_fill_coversheet, fdf_stream)

        # join coversheet with form
        combined_tmp = tempfile.NamedTemporaryFile()
        if mail_letter:
            # fill in letter template with mail_deadline
            letter_tmp = tempfile.NamedTemporaryFile()
            fdf_letter_stream = forge_fdf(fdf_data_strings=form_data)
            pdftk_fill_letter = [PDFTK_BIN,
                 self.letter_template, 'fill_form', '-',
                 'output', letter_tmp.name, 'flatten']
            self.run_subprocess(pdftk_fill_letter, fdf_letter_stream)

            pdftk_join = [PDFTK_BIN,
                         'C=%s' % coversheet_tmp.name, 'F=%s' % filled_form_tmp.name,
                         'L=%s' % letter_tmp.name,
                         'cat', 'L', 'C', 'F1-1',  # only include first page of filled_form
                         'output', combined_tmp.name]
        else:
            pdftk_join = [PDFTK_BIN,
                         'C=%s' % coversheet_tmp.name, 'F=%s' % filled_form_tmp.name,
                         'cat', 'C', 'F1-1',  # only include first page of filled_form
                         'output', combined_tmp.name]
        self.run_subprocess(pdftk_join)

        final_contents = combined_tmp.read()
        return final_contents

    def submit(self, user, error_callback_url=None):
        self.error_callback_url = error_callback_url

        try:
            form_data = self.match_fields(user)
            include_postage = user.get('include_postage', False)
            mail_letter = user.get('mail_letter', False)
            to_address = election_mail.get_mailto_address(user)
            pdf_file = self.generate_pdf(form_data, to_address, include_postage, mail_letter)

            if pdf_file:
                self.pdf_url = storage.upload_to_s3(pdf_file, 'forms/%s/hellovote-registration-print-me.pdf' % self.uid)

                if mail_letter:
                    letter = postage.mail_letter(self.uid, user, self.pdf_url)
                    return {'status': 'success',
                            'mail_letter': True,
                            'mail_carrier': letter.carrier,
                            'expected_delivery_date': letter.expected_delivery_date,
                            'pdf_url': self.pdf_url}
                else:
                    return {'status': 'success', 'pdf_url': self.pdf_url}
            else:
                return {'status': 'error', 'message': 'unable to generate NVRA pdf'}

        except ValidationError, e:
            raise OVRError(self, message=e.message, payload=e.payload, error_callback_url=self.error_callback_url)

        except Exception, e:
            ex_type, ex, tb = sys.exc_info()
            log.error(ex_type, ex, tb)
            raise OVRError(self, message="%s %s" % (ex_type, ex), payload=traceback.format_tb(tb), error_callback_url=self.error_callback_url)
