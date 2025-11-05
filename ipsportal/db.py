import logging
from typing import Any, TypedDict

from flask import Flask, g
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.database import Database
from werkzeug.local import LocalProxy

from .environment import MONGO_HOST, MONGO_PASSWORD, MONGO_PORT, MONGO_USERNAME

logger = logging.getLogger(__name__)


class EnsembleInformation(TypedDict):
    """A run can store a list of ensembles associated with it."""

    ensemble_id: str
    """This should be unique within the runs DB. This is sent by the parent when adding ensemble information, this is sent with child ensembles when actually saving them.

    Ensemble ids should be unique throughout the entire application.
    """
    component_name: str
    """
    Human-readable component name (set by domain scientist), should be unique per run
    """
    ensemble_name: str
    """
    Human-readable ensemble name (set by domain scientist), unique per run within a component
    """
    path: str
    """The path to the flat-file which stores the ensemble data"""


def get_db() -> Database[dict[str, Any]]:
    if 'db' not in g:
        client: MongoClient[dict[str, Any]] = MongoClient(
            host=MONGO_HOST,
            port=MONGO_PORT,  # type: ignore[arg-type]
            username=MONGO_USERNAME,
            password=MONGO_PASSWORD,
        )
        client.portal.runs.create_index([('runid', DESCENDING)], unique=True)
        client.portal.runs.create_index([('portal_runid', ASCENDING)], unique=True)
        client.portal.data.create_index([('runid', DESCENDING)], unique=True)
        # client.portal.data.create_index([('portal_runid', ASCENDING)], unique=True)
        g.db = client.portal

    return g.db  # type: ignore[no-any-return]


def close_db(_e: BaseException | None = None) -> None:
    db = g.pop('db', None)

    if db is not None:
        db.client.close()


def init_app(app: Flask) -> None:
    app.teardown_appcontext(close_db)


# Use LocalProxy to read the global db instance with just `db`
db: Database[dict[str, Any]] = LocalProxy(get_db)  # type: ignore[assignment]


def get_runs_total(db_filter: dict[str, Any]) -> int:
    return db.runs.count_documents(db_filter)


def get_runs(
    db_filter: dict[str, Any],
    skip: int | None = None,
    limit: int | None = None,
    sort: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    aggregation_pipeline: list[dict[str, Any]] = [
        {'$match': db_filter},
        {
            '$addFields': {
                'timeout': {
                    '$cond': [
                        {
                            '$and': [
                                {'$eq': ['$state', 'Running']},
                                {
                                    '$or': [
                                        {'$not': '$lastModified'},
                                        {
                                            '$gte': [
                                                {
                                                    '$dateDiff': {
                                                        'startDate': '$lastModified',
                                                        'endDate': '$$NOW',
                                                        'unit': 'hour',
                                                    }
                                                },
                                                3,
                                            ]
                                        },
                                    ]
                                },
                            ]
                        },
                        True,
                        False,
                    ]
                }
            }
        },
        {
            '$project': {
                '_id': False,
                'has_trace': True,
                'host': True,
                'ips_version': True,
                'lastModified': True,
                'ok': True,
                'parent_portal_runid': True,
                'portal_runid': True,
                'rcomment': True,
                'runid': True,
                'shotno': True,
                'sim_runid': True,
                'simname': True,
                'startat': True,
                'state': {'$cond': ['$timeout', 'Timeout', '$state']},
                'stopat': {'$cond': ['$timeout', {'$last': '$events.time'}, '$stopat']},
                'tag': True,
                'tokamak': True,
                'user': True,
                'walltime': True,
                'vizurl': True,
            }
        },
    ]
    if sort:
        aggregation_pipeline.append({'$sort': sort})
    if skip:
        aggregation_pipeline.append({'$skip': skip})
    if limit:
        aggregation_pipeline.append({'$limit': limit})

    # if the query is taking longer than 30 seconds (probably already too long), kill it to prevent a DDOS
    return list(db.runs.aggregate(aggregation_pipeline, maxTimeMS=30_000))


def get_events(db_filter: dict[str, Any]) -> list[dict[str, Any]] | None:
    runs = db.runs.find_one(db_filter, projection={'_id': False, 'events': True})
    if runs is None:
        return None
    return runs['events']  # type: ignore[no-any-return]


def get_run(db_filter: dict[str, Any]) -> dict[str, Any] | None:
    runs = get_runs(db_filter, limit=1)
    if runs:
        return runs[0]
    return None


def get_trace(db_filter: dict[str, Any]) -> list[dict[str, Any]]:
    runs = db.runs.find(filter=db_filter, projection={'_id': False, 'portal_runid': True, 'traces': True})
    traces = []
    for run in runs:
        traces += run['traces']
        portal_runid = run['portal_runid']
        traceId = run['traces'][-1]['traceId']

        # add all child traces
        for trace in get_trace({'parent_portal_runid': portal_runid}):
            trace['traceId'] = traceId
            traces.append(trace)

    return traces


def add_run(run: dict[str, Any]) -> Any:
    return db.runs.insert_one(run)


def update_run(db_filter: dict[str, Any], update: dict[str, Any]) -> Any:
    return db.runs.update_one(db_filter, update)


def get_runid(portal_runid: str) -> int | None:
    result = db.runs.find_one(filter={'portal_runid': portal_runid}, projection={'runid': True, '_id': False})
    if result:
        return result.get('runid')
    return None


def get_portal_runid(runid: int) -> str | None:
    result = db.runs.find_one(filter={'runid': runid}, projection={'portal_runid': True, '_id': False})
    if result:
        return result.get('portal_runid')
    return None


def get_parent_portal_runid(portal_runid: str) -> str | None:
    result = db.runs.find_one(
        filter={'portal_runid': portal_runid}, projection={'parent_portal_runid': True, '_id': False}
    )
    if result:
        return result.get('parent_portal_runid')
    return None


def get_runid_from_parent_portal_runid(parent_portal_runid: str) -> int | None:
    result = db.runs.find_one(
        filter={'parent_portal_runid': parent_portal_runid}, projection={'portal_runid': True, '_id': False}
    )
    if result:
        return result.get('portal_runid')
    return None


def next_runid() -> int:
    return int(db.runid.find_one_and_update({}, {'$inc': {'runid': 1}}, upsert=True, new=True).get('runid', 0))


def get_data_tags(portal_runid: str) -> dict[str, Any] | None:
    result = db.data.find_one({'portal_runid': portal_runid}, projection={'_id': False, 'tags': True})
    if result:
        return result.get('tags')
    return None


def get_data_information(
    runid: int,
) -> tuple[list[dict[str, Any]] | None, list[str] | None, list[EnsembleInformation] | None]:
    result = db.data.find_one(
        {'runid': runid}, projection={'_id': False, 'tags': True, 'jupyter_urls': True, 'ensembles': True}
    )
    if result:
        return result.get('tags'), result.get('jupyter_urls'), result.get('ensembles')
    return None, None, None


def get_ensembles(runid: int, ensemble_id: str | None = None) -> list[EnsembleInformation] | None:
    db_filter: dict[str, Any] = {'runid': runid}
    if ensemble_id:
        db_filter['ensembles'] = {
            '$elemMatch': {
                'ensemble_id': ensemble_id,
            }
        }
    result = db.data.find_one(db_filter, projection={'_id': False, 'ensembles': True})
    if result:
        return result.get('ensembles')
    return None


def get_parent_runid_by_child_runid(child_runid: int) -> int | None:
    """Try to get a parent runid from the child runid.

    If runid does not have a parent, return None
    """
    child_portal_runid_search = db.runs.find_one({'runid': child_runid}, {'parent_portal_runid': True, '_id': False})
    if not child_portal_runid_search:
        return None
    parent_portal_runid = child_portal_runid_search.get('parent_portal_runid')
    if not parent_portal_runid:
        return None

    return get_runid(parent_portal_runid)


def save_ensemble_file_path(runid: int, ensemble_id: str, component_name: str, ensemble_name: str, path: str) -> None:
    """The ensemble runner adds ensemble information.

    - runid: the ID of the run itself (the "parent")
    - ensemble_id: the ID of the ensemble we're tracking. This is tracked in child events
    - component_name: human-readable name of the component which launched the ensemble, which is set from the IPS framework (generally the config file) and used for visualizations
    - ensemble_name: human-readable name of the ensemble, set from the IPS framework's call to `run_ensemble` and used for visualizations
    - path: where we are saving the CSV to
    """
    db.data.update_one(
        {'runid': runid},
        {
            '$push': {
                'ensembles': {
                    'ensemble_id': ensemble_id,
                    'component_name': component_name,
                    'ensemble_name': ensemble_name,
                    'path': path,
                }
            }
        },
        upsert=True,
    )
