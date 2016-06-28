from __future__ import unicode_literals
from base_ovr_form import BaseOVRForm, OVRError
import json


class VoteDotOrg(BaseOVRForm):
    def __init__(self):
        super(VoteDotOrg, self).__init__('https://register.vote.org/')
        self.required_fields.extend(['political_party', 'email'])

    def parse_errors(self):
        messages = []
        for error in self.browser.find_all(class_='usa-alert-error'):
            messages.append(error.find(class_='usa-alert-body').text)
        return messages

    def get_started(self, user):
        form = self.browser.get_form(id='get_started_form')
        form['first_name'].value = user['first_name']
        form['last_name'].value = user['last_name']

        # date_of_birth -> parts
        (year, month, day) = self.split_date(user['date_of_birth'])
        form['date_of_birth_month'].value = month
        form['date_of_birth_day'].value = day
        form['date_of_birth_year'].value = year

        # street address
        # can't figure out how to bypass autocomplete, so reassemble parts into string
        form['address_autocomplete'] = '%(home_address)s %(home_city)s %(state)s %(home_zip)s' % user

        # contact
        form['email'] = user.get('email')
        form['mobile_phone'] = user['phone']

        self.log_form(form)
        self.browser.submit_form(form)

        return form

    def full_registration(self, user):
        # if given choice to register online, choose pdf form
        if self.browser.get_form(id='state_ovr'):
            finish_form = self.browser.get_form(id='finish')
            self.log_form(finish_form)
            self.browser.submit_form(finish_form)

        full_form = self.browser.get_form(id='full_registration')
        if full_form:
            # BUG, user.get(field, '') results in silent 400 errors, wtf?
            # full_form['title'].value = user.get('title', '')
            # print 'set title', full_form['title'].value
            # full_form['suffix'].value = user.get('suffix', '')
            # print 'set suffix', full_form['suffix'].value

            full_form['state_id_number'].value = user['id_number']

            # TODO, coerce free text party name to valid enum values
            full_form['political_party'].value = user.get('political_party')

            # convert boolean to '0' or '1'
            full_form['us_citizen'].value = str(int(user['us_citizen']))

            self.log_form(full_form)
            self.browser.submit_form(full_form)

        else:
            errors_string = ','.join(self.parse_errors())
            raise OVRError('unable to get_form full_registration: ' + errors_string, payload=self.browser.parsed)

    def get_download(self, user):
        self.browser.open('https://register.vote.org/downloads.json')
        download_response = self.browser.state.response.json()
        return download_response

    def submit(self, user):
        self.validate(user)
        self.get_started(user)
        self.full_registration(user)

        if self.browser.select('a#download_link'):
            return self.get_download(user)
        else:
            # log error?
            return {'status': 'unable to find download_link'}
