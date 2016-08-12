import psycopg2
import datetime
import json
import re
from flask import current_app


def init_db(app):
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    db = psycopg2.connect(app.config['DATABASE_URL'])

    # create table
    cur = db.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS logged_forms (id serial PRIMARY KEY, ts timestamp, state varchar, status json, parsed text); ")
    db.commit()

    app.db = db
    return app


def log_form(form, status):
    cur = current_app.db.cursor()
    sql = "INSERT INTO logged_forms (ts, state, status, parsed) VALUES ('{}','{}','{}','{}');"

    html = """%s""" % form.browser.state.response.content  # wrap in multi-line string until we escape it
    escaped_html = re.sub('[\"\']', '', html)              # remove quotes
    escaped_html = re.sub('[\n\r\t]', '', escaped_html)    # and whitespace
    escaped_html = json.dumps(escaped_html)                # let json escape everything else

    cur.execute(sql.format(
        datetime.datetime.now(),
        form.__class__.__name__,
        json.dumps(status),
        escaped_html
    ))
    current_app.db.commit()
