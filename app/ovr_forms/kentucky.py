from base_ovr_form import BaseOVRForm, OVRError
from form_utils import ValidationError, split_date, get_party_from_list, get_address_components, clean_browser_response
import sys, traceback


class Kentucky(BaseOVRForm):

    def __init__(self):
        super(Kentucky, self).__init__('https://vrsws.sos.ky.gov/ovrweb/')
        self.add_required_fields(['will_be_18', 'gender', 'ssn', 'political_party', 'incompetent', 'disenfranchised', 'claim_elsewhere'])
        self.success_string = 'Your Kentucky Voter Registration Application has been submitted'

    def submit(self, user, error_callback_url=None):

        self.error_callback_url = error_callback_url

        # KY doesn't have intermediate forms, they just submit as JSON all at once
        # assemble the data dict iteratively, to match style of other states
        form_data = {}

        try:
            steps = [
                self.requirements,
                self.check_existing,
                self.personal_information,
                self.party_affiliation,
                self.address,
                self.signature
            ]

            for handler in steps:
                handler(user, form_data)
            r = self.browser.session.post('https://vrsws.sos.ky.gov/EVRwcf/EVRwcf.Service1.svc/UpdateVoter', json=form_data,
                                      headers={'X-Requested-With': 'XMLHttpRequest',
                                               'Referer': 'https://vrsws.sos.ky.gov/ovrweb/'})
            success_page = r.content
            if self.success_string in success_page:
                return {'status': 'success'}
            else:
                raise ValidationError(message='no_success_string')

        except ValidationError, e:
            raise OVRError(self, message=e.message, payload=e.payload, error_callback_url=self.error_callback_url)

        except Exception, e:
            ex_type, ex, tb = sys.exc_info()
            raise OVRError(self, message="%s %s" % (ex_type, ex), payload=traceback.format_tb(tb), error_callback_url=self.error_callback_url)

    def requirements(self, user, form):
        # check answers to requirements, but don't actually submit to state
        if not user['us_citizen']:
            raise ValidationError(message='You must be a US citizen to register to vote in Kentucky')
        if not user['legal_resident']:
            raise ValidationError(message='You must be a current resident of Kentucky to register to vote')
        if not user['will_be_18']:
            raise ValidationError(message='You must be at least 18 years of age on or before the next general election.')
        if user['disenfranchised']:
            raise ValidationError(message='You must not be a convicted felon, or if your have been convicted of a felony, your civil rights must be restored by executive pardon.')
        if user['incompetent']:
            raise ValidationError(message='You must not have not been judged "mentally incompetent" in a court of law.')
        if user['claim_elsewhere']:
            raise ValidationError(message='You must not claim the right to vote anywhere outside Kentucky')

        # individual registration, not part of high school or college registration drive
        form['regsrc'] = 'in'

    def lookup_existing_record(self, form):
        if not form['ssn']:
            raise ValidationError(message='We need your Social Security number to look up your existing voter registration')
        if not form['dob']:
            raise ValidationError(message='We need your date of birth to look up your existing voter registration')

        form['ssn_no_sep'] = form['ssn'].replace('-', '')
        r = self.browser.session.get('https://vrsws.sos.ky.gov/EVRwcf/EVRwcf.Service1.svc/getVoterData/%(ssn_no_sep)s/%(dob)s' % form,
                             headers={'Referer': 'https://vrsws.sos.ky.gov/ovrweb/'})
        del form['ssn_no_sep']
        return r.json()

    def check_existing(self, user, form):
        (year, month, day) = split_date(user['date_of_birth'])
        form['dob'] = '-'.join([month, day, year])

        # re-insert dashes, which we removed
        form['ssn'] = '-'.join([user['ssn'][0:3], user['ssn'][3:5], user['ssn'][5:9]])

        form['driverslicense'] = user['state_id_number']

        voter_record = self.lookup_existing_record(form)
        if voter_record and voter_record['getVoterDataResult'][0]['ctr'] > 0:
            form['ctr'] = voter_record['getVoterDataResult'][0]['ctr']
        else:
            # TODO, create a new record
            pass

    def personal_information(self, user, form):
        form['fname'] = user.get('first_name').upper()
        form['mname'] = user.get('middle_name', '').upper()
        form['lname'] = user.get('last_name').upper()

        form['sex'] = user.get('gender')[0].upper()
        form['email'] = user.get('email', '')

    def party_affiliation(self, user, form):
        party_list = {
            "Democratic": "D",
            "Republican": "R",
            "Other": "O",
            "Constitution": "C",
            "Reform": "F",
            "Independent": "I",
            "Libertarian": "L",
            "Socialist Workers": "S",
            "Green": "G",
        }
        party_name = get_party_from_list(user['political_party'], party_list.keys())
        form['party'] = party_list[party_name]

    def address(self, user, form):
        address_components = get_address_components(user['address'], user['city'], user['state'], user['zip'])

        form['resstreetnumber'] = address_components['primary_number']

        street_name = address_components['street_name']
        if 'street_predirection' in address_components:
            street_name = "%s %s" % (address_components['street_predirection'], street_name)

        if 'street_postdirection' in address_components:
            street_name = "%s %s" % (street_name, address_components['street_postdirection'])

        form["resaddress"] = street_name.upper()

        form['rescity'] = user['city'].upper()
        form['resstate'] = user['state'].upper()
        form['reszip'] = user['zip']

        county_list = {"ADAIR": 1, "ALLEN": 2, "ANDERSON": 3, "BALLARD": 4, "BARREN": 5, "BATH": 6, "BELL": 7, "BOONE": 8, "BOURBON": 9, "BOYD":10, "BOYLE":11, "BRACKEN":12, "BREATHITT":13, "BRECKINRIDGE":14, "BULLITT":15, "BUTLER":16, "CALDWELL":17, "CALLOWAY":18, "CAMPBELL":19, "CARLISLE":20, "CARROLL":21, "CARTER":22, "CASEY":23, "CHRISTIAN":24, "CLARK":25, "CLAY":26, "CLINTON":27, "CRITTENDEN":28, "CUMBERLAND":29, "DAVIESS":30, "EDMONSON":31, "ELLIOTT":32, "ESTILL":33, "FAYETTE":34, "FLEMING":35, "FLOYD":36, "FRANKLIN":37, "FULTON":38, "GALLATIN":39, "GARRARD":40, "GRANT":41, "GRAVES":42, "GRAYSON":43, "GREEN":44, "GREENUP":45, "HANCOCK":46, "HARDIN":47, "HARLAN":48, "HARRISON":49, "HART":50, "HENDERSON":51, "HENRY":52, "HICKMAN":53, "HOPKINS":54, "JACKSON":55, "JEFFERSON":56, "JESSAMINE":57, "JOHNSON":58, "KENTON":59, "KNOTT":60, "KNOX":61, "LARUE":62, "LAUREL":63, "LAWRENCE":64, "LEE":65, "LESLIE":66, "LETCHER":67, "LEWIS":68, "LINCOLN":69, "LIVINGSTON":70, "LOGAN":71, "LYON":72, "MCCRACKEN":73, "MCCREARY":74, "MCLEAN":75, "MADISON":76, "MAGOFFIN":77, "MARION":78, "MARSHALL":79, "MARTIN":80, "MASON":81, "MEADE":82, "MENIFEE":83, "MERCER":84, "METCALFE":85, "MONROE":86, "MONTGOMERY":87, "MORGAN":88, "MUHLENBERG":89, "NELSON":90, "NICHOLAS":91, "OHIO":92, "OLDHAM":93, "OWEN":94, "OWSLEY":95, "PENDLETON":96, "PERRY":97, "PIKE":98, "POWELL":99, "PULASKI":100, "ROBERTSON":101, "ROCKCASTLE":102, "ROWAN":103, "RUSSELL":104, "SCOTT":105, "SHELBY":106, "SIMPSON":107, "SPENCER":108, "TAYLOR":109, "TODD":110, "TRIGG":111, "TRIMBLE":112, "UNION":113, "WARREN":114, "WASHINGTON":115, "WAYNE":116, "WEBSTER":117, "WHITLEY":118, "WOLFE":119, "WOODFORD":120}
        form['countycode'] = str(county_list[user['county'].upper()])

        # mailing address
        if user.get('has_separate_mailing_address'):
            # TODO
            pass
        else:
            # need to post nulls here
            form['mailaddress'] = None
            form['mailcity'] = None
            form['mailstate'] = None
            form['mailzip'] = None

    def signature(self, user, form):
        if user['consent_use_signature']:
            # verify null is the correct value for pulling sig from DMV
            form['msSig'] = None
