from typing import List, Dict, Any, Optional
from pymongo import MongoClient, ASCENDING, DESCENDING
from werkzeug.local import LocalProxy
from flask import g, Flask
import os


def get_db() -> Any:
    if 'db' not in g:
        client = MongoClient(host=os.environ.get('MONGO_HOST', 'localhost'),
                             port=int(os.environ.get('MONGO_PORT', 27017)),
                             username=os.environ.get('MONGO_USERNAME'),
                             password=os.environ.get('MONGO_PASSWORD'))
        client.portal.runs.create_index([('runid', DESCENDING)], unique=True)
        client.portal.runs.create_index([('portal_runid', ASCENDING)], unique=True)
        g.db = client.portal

    return g.db


def close_db(e: Optional[BaseException] = None) -> None:
    db = g.pop('db', None)

    if db is not None:
        db.client.close()


def init_app(app: Flask) -> None:
    app.teardown_appcontext(close_db)


# Use LocalProxy to read the global db instance with just `db`
db: LocalProxy = LocalProxy(get_db)


def get_runs(last_event: bool = False) -> List[Dict[str, Any]]:
    return list(db.runs.find(filter={'parent_portal_runid': None},
                             projection={'_id': False,
                                         'events': {'$slice': -1} if last_event else False,
                                         'traces': False}))


def get_child_runs(filter: Dict[str, Any], last_event: bool = False) -> List[Dict[str, Any]]:
    return list(db.runs.find(filter,
                             projection={'_id': False,
                                         'events': {'$slice': -1} if last_event else False,
                                         'traces': False}))


def get_events(filter: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    runs = db.runs.find_one(filter, projection={'_id': False, 'events': True})
    if runs is None:
        return None
    return runs['events']  # type: ignore[no-any-return]


def get_run(filter: Dict[str, Any]) -> Dict[str, Any]:
    return db.runs.find_one(filter,  # type: ignore[no-any-return]
                            projection={'_id': False, 'events': {'$slice': -1}, 'traces': False})


def get_trace(filter: Dict[str, Any]) -> List[Dict[str, Any]]:
    runs = db.runs.find(filter,
                        projection={'_id': False, 'portal_runid': True, 'traces': True})
    traces = []
    for run in runs:
        traces += run['traces']
        portal_runid = run["portal_runid"]
        traceId = run['traces'][-1]['traceId']

        # add all child traces
        for trace in get_trace({'parent_portal_runid': portal_runid}):
            trace['traceId'] = traceId
            traces.append(trace)

    return traces


def add_run(run: Dict[str, Any]) -> Any:
    return db.runs.insert_one(run)


def update_run(filter: Dict[str, Any], update: Dict[str, Any]) -> Any:
    return db.runs.update_one(filter, update)


def get_runid(portal_runid: str) -> Any:
    return db.runs.find_one(filter={'portal_runid': portal_runid},
                            projection={'runid': True, '_id': False}).get('runid')


def get_portal_runid(runid: int) -> Any:
    return db.runs.find_one(filter={'runid': runid},
                            projection={'portal_runid': True, '_id': False}).get('portal_runid')


def get_parent_portal_runid(portal_runid: str) -> Any:
    return db.runs.find_one(filter={'portal_runid': portal_runid},
                            projection={'parent_portal_runid': True, '_id': False}).get('parent_portal_runid')


def next_runid() -> int:
    return int(db.runid.find_one_and_update({}, {"$inc": {"runid": 1}}, upsert=True, new=True).get('runid', 0))
