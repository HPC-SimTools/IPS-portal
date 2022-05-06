import time
from flask import Blueprint, jsonify, request
import pymongo
from ipsportal.db import get_db

bp = Blueprint('api', __name__)


def db_runs(json=None):
    db = get_db()
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


@bp.route("/api/runs")
def runs():
    if request.is_json:
        return jsonify(db_runs(json=request.json))

    return jsonify(db_runs())


def runs_count():
    return get_db().runs.count_documents({})


def db_events_runid(runid):
    db = get_db()
    runs = db.runs.find_one({'runid': runid}, projection={'_id': False, 'events': True})
    if runs is None:
        return None
    return runs['events']


@bp.route("/api/run/<int:runid>/events")
def events_runid(runid):
    events = db_events_runid(runid)
    if events is None:
        return jsonify(message=f"runid {runid} not found"), 404

    return jsonify(events)


def db_run_runid(runid):
    db = get_db()
    return db.runs.find_one({'runid': runid}, projection={'_id': False, 'events': False, 'traces': False})


@bp.route("/api/run/<int:runid>")
def run_runid(runid):
    run = db_run_runid(runid)
    if run is None:
        return jsonify(message=f"runid {runid} not found"), 404
    return jsonify(run)


@bp.route("/api/run/<string:portal_runid>")
def run(portal_runid):
    db = get_db()
    run = db.runs.find_one({'portal_runid': portal_runid}, projection={'_id': False, 'events': False, 'traces': False})
    if run is None:
        return jsonify(message=f"portal_runid {portal_runid} not found"), 404
    return jsonify(run)


@bp.route("/api/run/<string:portal_runid>/events")
def events(portal_runid):
    db = get_db()
    run = db.runs.find_one({'portal_runid': portal_runid},
                           projection={'_id': False, 'events': True})
    if run is None:
        return jsonify(message=f"portal_runid {portal_runid} not found"), 404
    return jsonify(run['events'])


def db_trace_runid(runid):
    db = get_db()
    run = db.runs.find_one({'runid': runid},
                           projection={'_id': False, 'traces': True})
    if run is None:
        return None

    return run['traces']


@bp.route("/api/run/<int:runid>/trace")
def trace_runid(runid):
    traces = db_trace_runid(runid)
    if traces is None:
        return jsonify(message=f"runid {runid} not found"), 404

    return jsonify(traces)


@bp.route("/api/run/<string:portal_runid>/trace")
def trace(portal_runid):
    db = get_db()
    run = db.runs.find_one({'portal_runid': portal_runid},
                           projection={'_id': False, 'traces': True})
    if run is None:
        return jsonify(message=f"portal_runid {portal_runid} not found"), 404

    return jsonify(run['traces'])


@bp.route("/", methods=['POST'])
@bp.route("/api/event", methods=['POST'])
def event():
    e = request.json

    required = {'code', 'eventtype', 'comment', 'walltime', 'phystimestamp', 'portal_runid', 'seqnum'}
    run_keys = {'user', 'host', 'state', 'rcomment', 'tokamak', 'shotno', 'simname', 'startat',
                'stopat', 'sim_runid', 'outputprefix', 'tag', 'ips_version', 'portal_runid'}

    if not e.keys() >= required:
        return jsonify(message=f'Missing required data: {sorted(k for k in required if k not in e.keys())}'), 400

    e['created'] = time.strftime('%Y-%m-%d|%H:%M:%S%Z', time.localtime())

    db = get_db()

    if e.get('eventtype') == "IPS_START":
        runid = runs_count()
        run_dict = {key: e[key] for key in run_keys if key in e}
        run_dict['runid'] = runid
        run_dict['events'] = [e]
        run_dict['traces'] = []
        run_dict['has_trace'] = False
        try:
            db.runs.insert_one(run_dict)
        except pymongo.errors.DuplicateKeyError:
            return jsonify(message="Duplicate portal_runid Key"), 400
        return jsonify(message="New run created", runid=runid)

    if trace := e.pop('trace', False):
        if db.runs.find_one_and_update({'portal_runid': e.get('portal_runid')},
                                       {"$push": {"traces": trace}, "$set": {"has_trace": True}}) is None:
            return jsonify(message='Invalid portal_runid'), 400

    if db.runs.find_one_and_update({'portal_runid': e.get('portal_runid')}, {"$push": {"events": e}}) is None:
        return jsonify(message='Invalid portal_runid'), 400

    if e.get('eventtype') == "IPS_END":
        run_dict = {key: e[key] for key in run_keys if key in e}
        db.runs.find_one_and_update({'portal_runid': run_dict.get('portal_runid')}, {'$set': run_dict})
        return jsonify(message="Event added to run and run ended")

    return jsonify(message="Event added to run")
