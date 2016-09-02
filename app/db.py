import datetime
# from flask import current_app
import json
import psycopg2
from ovr_forms.form_utils import clean_browser_response
from config import DATABASE_URL


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    db = psycopg2.connect(DATABASE_URL)

    # create table
    cur = db.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS logged_forms (id serial PRIMARY KEY, uid varchar(255), ts timestamp, state varchar, status json, failed boolean default false, parsed text); ")
    cur.execute("CREATE INDEX IF NOT EXISTS logged_forms_uid on logged_forms (uid);")
    db.commit()

    return db


def log_response(form, status):
    db = get_db()
    cur = db.cursor()
    sql = "INSERT INTO logged_forms (ts, uid, state, status, failed, parsed) VALUES (NOW(), %s, %s, %s, %s, %s) RETURNING id;"
    cur.execute(sql, (
        str(form.get_uid()),
        form.__class__.__name__,
        json.dumps(status),
        True if "status" not in status or not status["status"] == "success" else False,
        str(form.browser.parsed) if form.browser._cursor > 0 else str(form.pdf_url)
    ))
    id_of_new_row = cur.fetchone()[0]

    db.commit()
    db.close()

    return id_of_new_row
