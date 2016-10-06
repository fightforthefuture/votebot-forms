from app.pdf_forms import postage
from app.pdf_forms import election_mail
from tests.run import BaseTestCase


class TestPostage(BaseTestCase):
    def setUp(self):
        super(TestPostage, self).setUp()

    def test_sos_address(self):
        state_addresses = election_mail.SOS_ADDRESS
        self.assertEqual(len(state_addresses.keys()), 51)


def create_sos_address_checks(state):
    def check_shipment(self):
        from_address = {
            'name': 'Josh Levinger',
            'street1': '1461 Alice St',
            'street2': '611',
            'city': 'Oakland',
            'state': 'CA',
            'zip': '94612'
        }
        to_address = election_mail.get_mailto_address({'state': state})
        assert to_address
        if 'street1' in to_address:
            shipment = postage.easypost_shipment(to_address, from_address)
            assert shipment.id is not None
            lowest_rate = shipment.lowest_rate()
            assert lowest_rate.carrier == 'USPS'
            assert lowest_rate.rate == '0.47'
        else:
            assert 'warning' in to_address
    return check_shipment

for state in election_mail.SOS_ADDRESS.keys():
    dynamic_method = create_sos_address_checks(state)
    dynamic_method.__name__ = 'test_sos_address_{0}'.format(state)
    setattr(TestPostage, dynamic_method.__name__, dynamic_method)
    # remove the last test so nose doesn't run it
    del dynamic_method
