from base_ovr_form import BaseOVRForm, OVRError


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
        try:
            year, month, day = user['date_of_birth'].split('-')
        except ValueError:
            raise OVRError('date must be in YYYY-MM-DD format')

        form['date_of_birth_month'].value = str(int(month))  # deal with zero-padding
        form['date_of_birth_day'].value = str(int(day))
        form['date_of_birth_year'].value = year

        # street address
        form['got_autocomplete'].options.extend('1')
        form['got_autocomplete'].value = '1'
        form['address_autocomplete'].value = ''
        form['street_address'].value = user['home_address']
        form['city'].value = user['home_city']
        form['state_abbr'].value = user['state']
        form['zip_5'].value = user['home_zip']

        # contact
        form['email'] = user.get('email')
        form['mobile_phone'] = user['phone']

        self.browser.submit_form(form)
        return form

    def full_registration(self, user):
        # if given choice to register online, choose pdf form
        if self.browser.get_form(id='state_ovr'):
            finish_form = self.browser.get_form(id='finish')
            self.browser.submit_form(finish_form)

        full_form = self.browser.get_form(id='full_registration')
        if full_form:
            full_form['title'].value = user.get('title', '')
            full_form['suffix'].value = user.get('suffix', '')
            full_form['state_id_number'].value = user['id_number']
            full_form['political_party'].value = user.get('political_party', '')
            full_form['us_citizen'].value = user['us_citizen']
            self.browser.submit_form(full_form)
        else:
            errors_string = ','.join(self.parse_errors())
            raise OVRError('unable to get_form full_registration: ' + errors_string)

    def submit(self, user):
        self.validate(user)
        self.get_started(user)
        self.full_registration(user)
        # check to see if pdf_url is present
        print self.browser.parsed
