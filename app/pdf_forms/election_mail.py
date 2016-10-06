import json
SOS_ADDRESS = json.load(open('app/pdf_forms/data/us_sos_address.json', 'r'))
NY_COUNTY_ADDRESS = json.load(open('app/pdf_forms/data/ny_county_address.json', 'r'))


def get_mailto_address(user):
    # TODO get local election offical address from Google Civic or US OVF
    # until then, just use statewide addresses from EAC

    state = user.get('state')
    county = user.get('county')

    # NY has specific county addresses they told us to use
    if state == 'NY' and county:
        ny_county_address = NY_COUNTY_ADDRESS.get(county.upper())
        if ny_county_address:
            return ny_county_address

    # statewide fallback
    return SOS_ADDRESS.get(state, None)
