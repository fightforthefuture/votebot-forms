from smartystreets.client import Client
from ..config import SMARTY_STREETS_AUTH_ID, SMARTY_STREETS_AUTH_TOKEN

from form_utils import ValidationError

US_STATES = {
    'AK': 'Alaska',
    'AL': 'Alabama',
    'AR': 'Arkansas',
    'AS': 'American Samoa',
    'AZ': 'Arizona',
    'CA': 'California',
    'CO': 'Colorado',
    'CT': 'Connecticut',
    'DC': 'District of Columbia',
    'DE': 'Delaware',
    'FL': 'Florida',
    'GA': 'Georgia',
    'GU': 'Guam',
    'HI': 'Hawaii',
    'IA': 'Iowa',
    'ID': 'Idaho',
    'IL': 'Illinois',
    'IN': 'Indiana',
    'KS': 'Kansas',
    'KY': 'Kentucky',
    'LA': 'Louisiana',
    'MA': 'Massachusetts',
    'MD': 'Maryland',
    'ME': 'Maine',
    'MI': 'Michigan',
    'MN': 'Minnesota',
    'MO': 'Missouri',
    'MP': 'Northern Mariana Islands',
    'MS': 'Mississippi',
    'MT': 'Montana',
    'NA': 'National',
    'NC': 'North Carolina',
    'ND': 'North Dakota',
    'NE': 'Nebraska',
    'NH': 'New Hampshire',
    'NJ': 'New Jersey',
    'NM': 'New Mexico',
    'NV': 'Nevada',
    'NY': 'New York',
    'OH': 'Ohio',
    'OK': 'Oklahoma',
    'OR': 'Oregon',
    'PA': 'Pennsylvania',
    'PR': 'Puerto Rico',
    'RI': 'Rhode Island',
    'SC': 'South Carolina',
    'SD': 'South Dakota',
    'TN': 'Tennessee',
    'TX': 'Texas',
    'UT': 'Utah',
    'VA': 'Virginia',
    'VI': 'Virgin Islands',
    'VT': 'Vermont',
    'WA': 'Washington',
    'WI': 'Wisconsin',
    'WV': 'West Virginia',
    'WY': 'Wyoming'
}

def get_address_components(address, city, state, zip):
    client = Client(auth_id=SMARTY_STREETS_AUTH_ID, auth_token=SMARTY_STREETS_AUTH_TOKEN)

    # reassemble components into string
    # smarty streets specifically wants strings (not unicode) so...
    full_address = "%(address)s, %(city)s, %(state)s, %(zip)s" % \
        {'address': str(address), 'city': str(city), 'state': str(state), 'zip': str(zip)}
    response = client.street_address(str(full_address))

    if not response or not response.get('analysis', False) or \
      response['analysis'].get('active', 'N') != 'Y':
        raise ValidationError("could not validate address", payload={
            "address": address,
            "city": city,
            "state": state,
            "zip": zip
            })

    # merge county into components dict
    d = response['components']
    d['county_name'] = response['metadata']['county_name']
    return d


def get_address_from_freeform(address):
    client = Client(auth_id=SMARTY_STREETS_AUTH_ID, auth_token=SMARTY_STREETS_AUTH_TOKEN)
    response = client.street_address(str(address))

    if not response or not response.get('analysis', False) or \
      response['analysis'].get('active', 'N') != 'Y':
        raise ValidationError("could not validate freeform address", payload={
            "address": address
            })

    return response


def get_street_name_from_components(address_components):
    street_name = address_components['street_name']
    if 'street_predirection' in address_components:
        street_name = "%s %s" % (address_components['street_predirection'], street_name)
    if 'street_suffix' in address_components:
        street_name += " %s" % address_components["street_suffix"]
    if 'street_postdirection' in address_components:
        street_name = "%s %s" % (street_name, address_components['street_postdirection'])
    return street_name


def get_street_address_from_components(address_components):
    return "%s %s" % (address_components['primary_number'], get_street_name_from_components(address_components))


def get_address_unit_from_components(address_components):
    address_unit = ''
    if address_components.get('secondary_number'):
        address_unit = address_components['secondary_number']
        if address_components.get('secondary_designator'):
            address_unit = "%s %s" % (address_components['secondary_designator'], address_unit)
    return address_unit


def state_abbr_to_name(abbr):
    return US_STATES.get(abbr)
