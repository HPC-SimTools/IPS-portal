import time
from flask import Blueprint, jsonify, request
import pymongo
from ipsportal.db import get_db

bp = Blueprint('api', __name__)

@bp.route("/api/runs")
def runs():
    db = get_db()
    runs = db.runs.find(projection={'_id': False, 'events': False, 'traces': False})
    return jsonify(list(runs))


@bp.route("/api/run/<int:runid>/events")
def events_runid(runid):
    db = get_db()
    events = db.runs.find_one({'runid': runid}, projection={'_id': False, 'events': True})
    if events is None:
        return jsonify(message=f"runid {runid} not found"), 404

    return jsonify(events['events'])


@bp.route("/api/run/<int:runid>")
def run_runid(runid):
    db = get_db()
    run = db.runs.find_one({'runid': runid}, projection={'_id': False, 'events': False, 'traces': False})
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


@bp.route("/api/run/<int:runid>/trace")
def trace_runid(runid):
    db = get_db()
    run = db.runs.find_one({'runid': runid},
                           projection={'_id': False, 'traces': True})
    if run is None:
        return jsonify(message=f"runid {runid} not found"), 404

    return jsonify(run['traces'])


@bp.route("/api/run/<string:portal_runid>/trace")
def trace(portal_runid):
    db = get_db()
    run = db.runs.find_one({'portal_runid': portal_runid},
                           projection={'_id': False, 'traces': True})
    if run is None:
        return jsonify(message=f"portal_runid {portal_runid} not found"), 404

    return jsonify(run['traces'])


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
        runid = db.runs.count_documents({})
        run_dict = {key: e[key] for key in run_keys if key in e}
        run_dict['runid'] = runid
        run_dict['events'] = [e]
        run_dict['traces'] = []
        try:
            db.runs.insert_one(run_dict)
        except pymongo.errors.DuplicateKeyError:
            return jsonify(message="Duplicate portal_runid Key"), 400
        return jsonify(message="New run created", runid=runid)

    if trace := e.pop('trace', False):
        if db.runs.find_one_and_update({'portal_runid': e.get('portal_runid')}, {"$push": {"traces": trace}}) is None:
            return jsonify(message='Invalid portal_runid'), 400

    if db.runs.find_one_and_update({'portal_runid': e.get('portal_runid')}, {"$push": {"events": e}}) is None:
        return jsonify(message='Invalid portal_runid'), 400

    if e.get('eventtype') == "IPS_END":
        run_dict = {key: e[key] for key in run_keys if key in e}
        db.runs.find_one_and_update({'portal_runid': run_dict.get('portal_runid')}, {'$set': run_dict})
        return jsonify(message="Event added to run and run ended")

    return jsonify(message="Event added to run")
