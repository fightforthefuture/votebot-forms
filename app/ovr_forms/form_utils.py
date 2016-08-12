from smartystreets.client import Client
from base_ovr_form import OVRError

import datetime
import difflib
import json
import re


# todo: this should really come from teh app.config object itself
# but I am in Python import hell with this for some reason.
# from app import app

# so pull the values themselves
from app.config import SMARTY_STREETS_AUTH_ID, SMARTY_STREETS_AUTH_TOKEN


#  TODO, move some of these into a fork of robobrowser?


def log_form(form):
    payload = form.serialize()
    serialized = payload.to_requests('POST')
    return serialized


def clean_browser_response(browser):
    html = """%s""" % browser.state.response.content  # wrap in multi-line string until we escape it
    escaped_html = re.sub('[\"\']', '', html)              # remove quotes
    escaped_html = re.sub('[\n\r\t]', '', escaped_html)    # and whitespace
    escaped_html = json.dumps(escaped_html)                # let json escape everything else
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
            raise OVRError('date must be in YYYY-MM-DD format')


def bool_to_string(boolean, capitalize=False):
    if boolean is None:
        raise OVRError("boolean shouldn't be None")
    r = str(boolean)
    if capitalize:
        return r.capitalize()
    else:
        return r.lower()


def bool_to_int(boolean):
    if boolean is None:
        raise OVRError("boolean shouldn't be None")
    r = int(boolean)
    return r


def get_address_components(address, city, state, zip):
    client = Client(auth_id=SMARTY_STREETS_AUTH_ID, auth_token=SMARTY_STREETS_AUTH_TOKEN)

    # smarty streets specifically wants strings (not unicode) so...
    response = client.street_address("%(address)s, %(city)s, %(state)s, %(zip)s" % \
                                    {'address': str(address), 'city': str(city), 'state': str(state), 'zip': str(zip)})

    if not response or not response.get('analysis', False) or \
        response['analysis'].get('active', 'N') != 'Y':
        raise OVRError("could not validate address")

    return response['components']


def get_party_from_list(party, party_list):

    # todo: we should normalize presence / abence of the word "Party"

    # common misspellings / too short to catch
    if party.lower() in ['dem', 'd']:
        party = 'Democratic'

    elif party.lower().strip() in ['r', 'gop', 'rep', 'repub', 'g.o.p.', 'grand old party']:
        party = 'Republican'

    try:
        return difflib.get_close_matches(party, party_list)[0]
    except IndexError:
        try:
            return filter(lambda p: party.lower() in p.lower(), party_list)[0]
        except IndexError:
            # need some kind of graceful fallback here.
            return None
