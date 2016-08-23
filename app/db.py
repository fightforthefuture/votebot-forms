import datetime
from flask import current_app
import json
import psycopg2
from ovr_forms.form_utils import clean_browser_response


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


def log_response(form, status):
    if current_app.db.closed:
        init_db(current_app)

    cur = current_app.db.cursor()
    sql = "INSERT INTO logged_forms (ts, state, status, parsed) VALUES ('{}','{}','{}','{}');"
    cur.execute(sql.format(
        datetime.datetime.now(),
        form.__class__.__name__,
        json.dumps(status),
        clean_browser_response(form.browser)
    ))
    current_app.db.commit()
