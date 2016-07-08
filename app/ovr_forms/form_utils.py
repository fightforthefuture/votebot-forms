from smartystreets.client import Client
from base_ovr_form import OVRError

# todo: this should really come from teh app.config object itself
# but I am in Python import hell with this for some reason.
# from app import app

# so pull the values themselves
from app.config import SMARTY_STREETS_AUTH_ID, SMARTY_STREETS_AUTH_TOKEN


#  TODO, move some of these into a fork of robobrowser?


def log_form(form):
    payload = form.serialize()
    serialized = payload.to_requests('POST')
    print serialized


def options_dict(field):
    return dict(zip(field.labels, field.options))


def split_date(date_string, padding=True):
    """ Expects date as YYYY-MM-DD, returns (year, month, day) tuple of strings.
        Performs zfill to ensure zero-padding for month, day.
    """
    try:
        (year, month, day) = date_string.split('-')

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


def get_address_components(home_address, home_city, state, home_zip):
    client = Client(auth_id=SMARTY_STREETS_AUTH_ID, auth_token=SMARTY_STREETS_AUTH_TOKEN)

    response = client.street_address("%(home_address)s, %(home_city)s, %(state)s, %(home_zip)s" % \
                                    {'home_address': home_address, 'home_city': home_city, 'state': state, 'home_zip': home_zip})

    if not response or not response.get('analysis', False) or \
        response['analysis'].get('active', 'N') != 'Y':
        raise OVRError("could not validate address")

    return response['components']

