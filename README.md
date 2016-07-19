# VoteBot-Forms

## Motivation
Online voter registration should be easy. Unfortunately, each state has their own form design. This application provides a nice API that abstracts across them, and falls back to the National Voter Registration Form when online registration is not possible.

## Usage
POST to '/registration' with json like
```
{ 
    "first_name":"John",
    "middle_name":"Q",
    "last_name":"Public",
    "date_of_birth":"1950-12-25",
    "home_address":"314 Test St",
    "home_city":"Schenectady",
    "state":"NY",
    "home_zip":"12345",
    "phone":"123-456-7890",
    "email":"text@example.com"
    "id_number":"NONE",
    "political_party":"No Party",
    "us_citizen":true,
    "not_a_felon":true,
}
```

receive a response like
```
{
    "status": "ready",
    "pdf_url": "https://ldv-bullwinkle-production.s3.amazonaws.com/voter_registration_forms/user_XXXXXX_YYYYMMDDHHMMSS_HASH.pdf?access_token" // for print and mail
}
```

## Development
- `virtualenv .venv; source .venv/bin/activate`
- `pip install -r requirements/development.txt`
- `python manager.py runserver`

## Testing
- fill `tests/secrets.yml` with valid identification information. ensure dates are iso-formatted strings
- eg `
    NY: 
      first_name: John
      middle_name: Q
      last_name: Public
      date_of_birth: "1950-12-25"
      home_address: 314 Test St
      home_city: Schenectady
      state: NY
      home_zip: 12345
      phone: 123-456-7890
      email: text@example.com
      id_number: NONE
      political_party: No Party
      us_citizen:true
      not_a_felon:true
`
- run `python tests/run.py`

## Security
- Requires PyOpenSSL and ndg-httpsclient for improved SSL certificate validation. California's system won't validate without it...

## Deployment
- run on Heroku under uwsgi w/ gevent
- TBD
