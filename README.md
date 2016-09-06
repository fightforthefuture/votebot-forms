# VoteBot-Forms

## Motivation
Online voter registration should be easy. Unfortunately, each state has their own form design. This application provides a nice API that abstracts across them, and falls back to the National Mail Voter Registration Form PDF when online registration is not possible.

## Usage
POST to '/registration' with json like
```
{ 
  callback_url: '/callback',
  user: {
    "first_name":"John",
    "middle_name":"Q",
    "last_name":"Public",
    "date_of_birth":"1950-12-25",
    "address":"314 Test St",
    "address_unit": "#1"
    "city":"Schenectady",
    "state":"NY",
    "zip":"12345",
    "phone":"123-456-7890",
    "email":"text@example.com"
    "state_id_number":"NONE",
    "ssn_last4": 0000,
    "political_party":"No Party",
    "us_citizen":true,
    "legal_resident": true,
    "disenfranchised":false,
  }
}
```

receive a response like
```
{
    "status": "queued"
}
```

get a POST to your callback_url like
```
{
    "status": "success", // for print and mail
    "pdf_url": "https://hellovote.s3.amazonaws.com/print/UUID.pdf?access_token"
}
```
or 
```
{
    "status": "success", // for state OVR
    "missing_fields": []
}
```

## Development
- `virtualenv .venv; source .venv/bin/activate`
- `pip install -r requirements/development.txt`
- `python manager.py runserver`
- in another terminal `python manager.py rq worker`

## Adding new states
Votebot-forms can only work with states that have online voter registration systems (OVR) without access control (user login, captcha, etc). Because we are submitting on behalf of the user, we will not do any work to circumvent access controls. 

To create a new state integration:

- add a new file called STATE.py to `app/ovr_forms`
- create a class that inherits from `BaseOVRForm`
- add required fields, making sure to match the [field taxonomy](https://docs.google.com/a/fightforthefuture.org/spreadsheets/d/11MoK-p-yOpZGrQ0-Y-_Ffdm1T4niYtsSut4UC6U60FQ/edit). If you need to define a new field, you'll also need to add it to votebot-api, to make sure we are asking users with the correct phrasing.
- start the state submission process in a browser, and get as far as you can without a local ID
- finish the form with a volunteer's ID, after getting one from the FFTF volunteer coordinator
- add unit tests to `tests/ovr_forms/test_STATE.py`
- when the form is tested, add it to the OVR_FORMS dict in `app/ovr_forms/__init__.py`

## PDF Form
The PDF form is generated from the [National Mail Voter Registration Form](http://www.eac.gov/voter_resources/register_to_vote.aspx), with a custom instructions and mailing page. These are combined with PDFTK, and filled in with an FDF data stream before being uploaded to Amazon S3 for user download. If changes are made to the instructions or mailing page, regenerate the combined template file with `pdftk A=coversheet.pdf B=eac-nvra.pdf cat A B1 output combined-template.pdf`

## Testing
- fill `tests/secrets.yml` with valid identification information. ensure dates are iso-formatted strings
- eg `
    NY: 
      first_name: John
      middle_name: Q
      last_name: Public
      date_of_birth: "1950-12-25"
      address: 314 Test St
      city: Schenectady
      state: NY
      zip: 12345
      phone: 123-456-7890
      email: text@example.com
      state_id_number: NONE,
      ssn_last4: 0000,
      political_party: No Party
      us_citizen:true
      legal_resident:true
      disenfranchised:false
`
- run `python tests/run.py`

## Security
- Requires PyOpenSSL and ndg-httpsclient for improved SSL certificate validation. California's system won't validate without it...

## Deployment
- run on Heroku under uwsgi w/ gevent
- use included compiled pdftk 2.02 binaries with
  `heroku config:set LD_LIBRARY_PATH=/app/.heroku/vendor/lib:/app/vendor/pdftk/lib`
  `heroku config:set PATH=/app/.heroku/python/bin:/usr/local/bin:/usr/bin:/bin:/app/vendor/pdftk/bin`
