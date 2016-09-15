import json
SOS_ADDRESS = json.load(open('app/pdf_forms/sos_address.json', 'r'))


def get_mailto_address(state):
    # TODO get local election offical address from Google Civic or US OVF
    # until then, just use statewide addresses from EAC
    return SOS_ADDRESS.get(state, None)
