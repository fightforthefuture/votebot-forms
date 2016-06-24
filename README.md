# VoteBot-Forms

## Motivation
Online voter registration should be easy. Unfortunately, each state has their own form design. This application provides a nice API that abstracts across them, and falls back to the National Voter Registration Form when online registration is not possible.

## Development
- `virtualenv .venv; source .venv/binactivate`
- `pip install -r requirements/development.txt`
- `python manager.py runserver`

## Security
- Requires PyOpenSSL and ndg-httpsclient for improved SSL certificate validation. California's system won't validate without it...

## Deployment
- run on Heroku under uwsgi w/ gevent
- TBD
