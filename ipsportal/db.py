from pymongo import MongoClient, ASCENDING, DESCENDING
from werkzeug.local import LocalProxy
from flask import g
import os


def get_db():
    if 'db' not in g:
        client = MongoClient('mongodb://'+os.environ.get('MONGODB_HOSTNAME', 'localhost')+':27017')
        client.portal.runs.create_index([('runid', DESCENDING)], unique=True)
        client.portal.runs.create_index([('portal_runid', ASCENDING)], unique=True)
        g.db = client.portal

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.client.close()


def init_app(app):
    app.teardown_appcontext(close_db)


# Use LocalProxy to read the global db instance with just `db`
db = LocalProxy(get_db)


def get_runs(json=None):
    if json:
        limit = json.get('per_page', 20)
        skip = (json.get('page', 1)-1) * limit
        sort_by = json.get('sort_by', 'runid')
        sort_direction = json.get('sort_direction', -1)
        runs = db.runs.find(skip=skip, limit=limit,
                            projection={'_id': False, 'events': False, 'traces': False}
                            ).sort(sort_by, sort_direction)
    else:
        runs = db.runs.find(projection={'_id': False, 'events': False, 'traces': False})
    return list(runs)


def runs_count():
    return db.runs.count_documents({})


def get_events(filter):
    runs = db.runs.find_one(filter, projection={'_id': False, 'events': True})
    if runs is None:
        return None
    return runs['events']


def get_run(filter):
    return db.runs.find_one(filter, projection={'_id': False, 'events': False, 'traces': False})


def get_trace(filter):
    run = db.runs.find_one(filter,
                           projection={'_id': False, 'traces': True})
    if run is None:
        return None

    return run['traces']


def add_run(run):
    return db.runs.insert_one(run)


def update_run(filter, update):
    return db.runs.update_one(filter, update)
