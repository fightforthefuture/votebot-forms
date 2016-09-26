import os
import requests
import easypost
import lob

easypost.api_key = os.environ.get('EASYPOST_API_KEY')
lob.api_key = os.environ.get('LOB_API_KEY')


def easypost_shipment(to_address, from_address):
    shipment = easypost.Shipment.create(
        to_address=to_address,
        from_address=from_address,
        parcel={
            "predefined_package": "Letter",
            "weight": 1.0
        },
        options={'label_format': 'PDF'}
    )
    return shipment


def buy_mailing_label(to_address, from_address):
    postage = easypost_shipment(to_address, from_address)
    rate = postage.lowest_rate(carriers=['USPS'], services=['First'])

    # ensure rate is USPS first class
    if rate.carrier == "USPS" and rate.service == "First":
        try:
            result = postage.buy(rate=rate)
            label_pdf_url = result.postage_label.label_pdf_url

            # get the file contents from the url
            response = requests.get(label_pdf_url)
            return response.content
        except easypost.Error:
            print "unable to buy postage", rate
            return None
    else:
        print "bad rate", rate
        return None


def mail_letter(id, user, file):
    to_address = {
        "name": "{first_name} {last_name}".format(**user)[:50],
        "address_line1": "{address} {unit}".format(
            address=user.get('address'),
            unit=user.get('address_unit', '')  # default to avoid KeyError
        ).strip()[:50],
        "address_city": user['city'],
        "address_state": user['state'],
        "address_zip": user['zip'],
        "address_country": 'US'
    }

    letter = lob.Letter.create(
        description='HelloVote Registration %s' % id,
        to_address=to_address,
        from_address={
            'name': 'HelloVote',
            'address_line1': 'PO Box 55071 #95005',
            'address_city': 'Boston',
            'address_state': 'MA',
            'address_zip': '02205',
            'address_country': 'US'
        },
        file=file,
        address_placement="top_first_page",
        double_sided=True,
        color=False
    )
    return letter
