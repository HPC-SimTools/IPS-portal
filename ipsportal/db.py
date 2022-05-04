from pymongo import MongoClient, ASCENDING, DESCENDING
from flask import g
import os


def get_db():
    if 'db' not in g:
        client = MongoClient('mongodb://'+os.environ.get('MONGODB_HOSTNAME', 'localhost')+':27017')
        client.portal.run.create_index([('runid', DESCENDING)], unique=True)
        client.portal.run.create_index([('portal_runid', ASCENDING)], unique=True)
        g.db = client.portal

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.client.close()


def init_app(app):
    app.teardown_appcontext(close_db)
