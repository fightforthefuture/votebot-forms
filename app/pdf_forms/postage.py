import os
import requests
import easypost

easypost.api_key = os.environ.get('EASYPOST_API_KEY')


def easypost_shipment(to_address, from_address):
    shipment = easypost.Shipment.create(
        to_address=to_address,
        from_address=from_address,
        parcel={
            "predefined_package": "Letter",
            "weight": 1.0
        },
    )
    return shipment


def buy_mailing_label(from_address, to_address):
    postage = easypost_shipment(to_address, from_address)
    result = postage.buy(rate=postage.lowest_rate())
    label_url = result.postage_label.label_url

    # get the file contents from the url
    response = requests.get(label_url)
    return response.content
