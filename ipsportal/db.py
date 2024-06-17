from typing import List, Dict, Any, Optional
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database
from werkzeug.local import LocalProxy
from flask import g, Flask
import os


def get_db() -> Database[Dict[str, Any]]:
    if 'db' not in g:
        client: MongoClient[Dict[str, Any]] = MongoClient(
                             host=os.environ.get('MONGO_HOST', 'localhost'),
                             port=int(os.environ.get('MONGO_PORT', 27017)),
                             username=os.environ.get('MONGO_USERNAME'),
                             password=os.environ.get('MONGO_PASSWORD'))
        client.portal.runs.create_index([('runid', DESCENDING)], unique=True)
        client.portal.runs.create_index([('portal_runid', ASCENDING)], unique=True)
        client.portal.data.create_index([('runid', DESCENDING)], unique=True)
        client.portal.data.create_index([('portal_runid', ASCENDING)], unique=True)
        g.db = client.portal

    return g.db  # type: ignore[no-any-return]


def close_db(e: Optional[BaseException] = None) -> None:
    db = g.pop('db', None)

    if db is not None:
        db.client.close()


def init_app(app: Flask) -> None:
    app.teardown_appcontext(close_db)


# Use LocalProxy to read the global db instance with just `db`
db: Database[Dict[str, Any]] = LocalProxy(get_db)  # type: ignore[assignment]


def get_runs_total(db_filter: Dict[str, Any]) -> int:
    return db.runs.count_documents(db_filter)


def get_runs(
        db_filter: Dict[str, Any],
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        sort: Optional[Dict[str, int]] = None,
) -> List[Dict[str, Any]]:
    aggregation_pipeline: List[Dict[str, Any]] = [
            {"$match": db_filter},
            {"$addFields": {
                "timeout": {"$cond":
                            [
                                {"$and": [{"$eq": ["$state", "Running"]},
                                          {"$or": [
                                              {"$not": "$lastModified"},
                                              {"$gte": [{"$dateDiff":
                                                         {"startDate": "$lastModified",
                                                          "endDate": "$$NOW",
                                                          "unit": "hour"}}, 3]}
                                          ]}]},
                                True, False]}
            }
             },
            {"$project": {
                "_id": False,
                "has_trace": True,
                "host": True,
                "ips_version": True,
                "lastModified": True,
                "ok": True,
                "parent_portal_runid": True,
                "portal_runid": True,
                "rcomment": True,
                "runid": True,
                "shotno": True,
                "sim_runid": True,
                "simname": True,
                "startat": True,
                "state": {"$cond": ["$timeout", "Timeout", "$state"]},
                "stopat": {"$cond": ["$timeout", {"$last": "$events.time"}, "$stopat"]},
                "tag": True,
                "tokamak": True,
                "user": True,
                "walltime": True,
                "vizurl": True
            }}
        ]
    if sort:
        aggregation_pipeline.append({'$sort': sort})
    if skip:
        aggregation_pipeline.append({'$skip': skip})
    if limit:
        aggregation_pipeline.append({'$limit': limit})

    # if the query is taking longer than 30 seconds (probably already too long), kill it to prevent a DDOS
    return list(db.runs.aggregate(aggregation_pipeline, maxTimeMS=30_000))


def get_events(db_filter: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    runs = db.runs.find_one(db_filter, projection={'_id': False, 'events': True})
    if runs is None:
        return None
    return runs['events']  # type: ignore[no-any-return]


def get_run(db_filter: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    runs = get_runs(db_filter, limit=1)
    if runs:
        return runs[0]
    return None


def get_trace(db_filter: Dict[str, Any]) -> List[Dict[str, Any]]:
    runs = db.runs.find(filter=db_filter,
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


def update_run(db_filter: Dict[str, Any], update: Dict[str, Any]) -> Any:
    return db.runs.update_one(db_filter, update)


def get_runid(portal_runid: str) -> Any:
    result = db.runs.find_one(
        filter={'portal_runid': portal_runid},
        projection={'runid': True, '_id': False}
    )
    if result:
        return result.get('runid')
    return None


def get_portal_runid(runid: int) -> Any:
    result = db.runs.find_one(
        filter={'runid': runid},
        projection={'portal_runid': True, '_id': False}
    )
    if result:
        return result.get('portal_runid')
    return None


def get_parent_portal_runid(portal_runid: str) -> Any:
    result = db.runs.find_one(
        filter={'portal_runid': portal_runid},
        projection={'parent_portal_runid': True, '_id': False}
    )
    if result:
        return result.get('parent_portal_runid')
    return None


def next_runid() -> int:
    return int(db.runid.find_one_and_update({}, {"$inc": {"runid": 1}}, upsert=True, new=True).get('runid', 0))


def get_data_tags(portal_runid: str) -> Optional[dict[str, Any]]:
    result = db.data.find_one(
        {"portal_runid": portal_runid}, projection={"_id": False, "tags": True}
    )
    if result:
        return result.get('tags')
    return None
