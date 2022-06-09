from pymongo import MongoClient, ASCENDING, DESCENDING
from werkzeug.local import LocalProxy
from flask import g
import os


def get_db():
    if 'db' not in g:
        client = MongoClient(host=os.environ.get('MONGO_HOST', 'localhost'),
                             port=os.environ.get('MONGO_PORT', 27017),
                             username=os.environ.get('MONGO_USERNAME'),
                             password=os.environ.get('MONGO_PASSWORD'))
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


def get_runs():
    return list(db.runs.find(projection={'_id': False, 'events': False, 'traces': False}))


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


def get_datafiles(filter):
    datafiles = db.runs.aggregate([{"$match": filter},
                                   {"$unwind": "$events"},
                                   {"$match": {"events.eventtype": "MONITOR_DATAFILE"}},
                                   {"$group": {"_id": "$_id",
                                               "datafiles": {"$addToSet": "$events.comment"}}}])

    try:
        return next(datafiles)['datafiles']
    except StopIteration:
        return []


def add_run(run):
    return db.runs.insert_one(run)


def update_run(filter, update):
    return db.runs.update_one(filter, update)
