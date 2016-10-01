import datetime
import difflib
import json
import re


def log_form(form):
    payload = form.serialize()
    serialized = payload.to_requests('POST')
    return serialized


def clean_browser_response(browser):
    html = """%s""" % browser.state.response.content  # wrap in multi-line string until we escape it
    escaped_html = re.sub('[\"\']', '', html)              # remove quotes
    escaped_html = re.sub('[\n\r\t]', '', escaped_html)    # and whitespace
    escaped_html = json.dumps(escaped_html, ensure_ascii=False)  # let json escape everything else
    return escaped_html


def clean_sensitive_info(user, keys=['state_id_number', 'ssn_last4']):
    new_dict = user.copy()
    for k in keys:
        try:
            new_dict.pop(k)
        except KeyError:
            continue
    return new_dict


def options_dict(field):
    return dict(zip(field.labels, field.options))


def split_date(date, padding=True):
    """ Expects date as YYYY-MM-DD, returns (year, month, day) tuple of strings.
        Performs zfill to ensure zero-padding for month, day.
    """
    if type(date) in [type(datetime.datetime), type(datetime.date)]:
        return (date.year, date.month, date.day)
    else:
        try:
            (year, month, day) = date.split('-')

            # there's a Y2k bug lurking here for 2020...
            # todo: centralize / standardize how to handle and submit dates
            if len(year) == 2:
                year = '19%s' % year

            if padding:
                month = month.zfill(2)
                day = day.zfill(2)
            else:
                if month.startswith('0'):
                    month = month[1]
                if day.startswith('0'):
                    day = day[1]
            return (year, month, day)
        except:
            raise ValidationError('date must be in YYYY-MM-DD format', payload=date)


def split_name(full_name):
    # really naive way of splitting name to (first, middle, last)
    previous_name_space_count = full_name.count(' ')
    previous_name_split = full_name.split(' ', 2)

    if previous_name_space_count == 0:
        # JLEV HACK
        # if a person has only one name, is it their last or first?
        first_name = ''
        middle_name = ''
        last_name = previous_name_split[0]
    elif previous_name_space_count == 1:
        first_name = previous_name_split[0]
        middle_name = ''
        last_name = previous_name_split[1]
    elif previous_name_space_count == 2:
        first_name = previous_name_split[0]
        middle_name = previous_name_split[1]
        last_name = previous_name_split[2]
    else:
        first_name = previous_name_split[0]
        middle_name = previous_name_split[1]
        last_name = ' '.join(previous_name_split[2:])

    return (first_name, middle_name, last_name)


def parse_gender(string):
    # expects male/female and coerces to M/F
    # other values raise ValidationError, because most state forms are binary
    # I know, it sucks
    if string.lower() == 'female':
        return 'F'
    if string.lower() == 'male':
        return 'M'
    else:
        raise ValidationError("unable to coerce gender to M/F", payload=string)


def bool_to_string(boolean, capitalize=False):
    if boolean is None:
        raise ValidationError("boolean shouldn't be None", payload=boolean)
    r = str(boolean)
    if capitalize:
        return r.capitalize()
    else:
        return r.lower()


def bool_to_int(boolean):
    if boolean is None:
        raise ValidationError("boolean shouldn't be None", payload=boolean)
    r = int(boolean)
    return r


def coerce_string_to_list(string, valid_list):
    try:
        return difflib.get_close_matches(string, valid_list)[0]
    except IndexError:
        try:
            return filter(lambda e: string.lower() in e.lower(), valid_list)[0]
        except IndexError:
            return None


def get_party_from_list(party, party_list=None):
    if not party_list:
        party_list = ["democrat", "republican", "libertarian", "green", "reform", "other"]

    # common misspellings / too short to catch / translations of common names
    if party.lower() in ['dem', 'd']:
        party = 'Democratic'

    elif party.lower().strip() in ['r', 'gop', 'rep', 'repub', 'g.o.p.', 'grand old party']:
        party = 'Republican'

    elif party.lower().strip() in ['lib', 'libertario']:
        party = 'Libertarian'

    elif party.lower().strip() in ['green', 'verde']:
        party = 'Green'

    return coerce_string_to_list(party, party_list)


def get_ethnicity_from_list(ethnicity, ethnicity_list=None):
    # list we offer in votebot-api
    if not ethnicity_list:
        ethnicity_list = ["asian-pacific", "black", "hispanic", "native-american", "white", "multi-racial", "other"]
    # todo, handle spanish?
    # asiatico o isleno del pacifico/negro/hispano/indigena norteamericano/blanco/multi-racial/otro
    return coerce_string_to_list(ethnicity, ethnicity_list)


class ValidationError(Exception):
    status_code = 400

    def __init__(self, message, payload=None):
        self.message = message
        self.payload = payload
