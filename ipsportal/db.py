from pymongo import MongoClient
from flask import g
import os


def get_db():
    if 'db' not in g:
        client = MongoClient('mongodb://'+os.environ.get('MONGODB_HOSTNAME', 'localhost')+':27017')
        g.db = client.portal

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.client.close()


def init_app(app):
    app.teardown_appcontext(close_db)
