import time
from flask import Blueprint, jsonify, request
import pymongo
from ipsportal.db import get_runs, runs_count, get_events, get_run, get_trace, add_run, update_run

bp = Blueprint('api', __name__)


@bp.route("/api/runs")
def runs():
    return jsonify(get_runs())


@bp.route("/api/run/<int:runid>/events")
def events_runid(runid):
    events = get_events({'runid': runid})
    if events is None:
        return jsonify(message=f"runid {runid} not found"), 404

    return jsonify(events)


@bp.route("/api/run/<int:runid>")
def run_runid(runid):
    run = get_run({'runid': runid})
    if run is None:
        return jsonify(message=f"runid {runid} not found"), 404
    return jsonify(run)


@bp.route("/api/run/<string:portal_runid>")
def run(portal_runid):
    run = get_run({'portal_runid': portal_runid})
    if run is None:
        return jsonify(message=f"portal_runid {portal_runid} not found"), 404
    return jsonify(run)


@bp.route("/api/run/<string:portal_runid>/events")
def events(portal_runid):
    events = get_events({'portal_runid': portal_runid})
    if events is None:
        return jsonify(message=f"portal_runid {portal_runid} not found"), 404
    return jsonify(events)


@bp.route("/api/run/<int:runid>/trace")
def trace_runid(runid):
    trace = get_trace({'runid': runid})
    if trace is None:
        return jsonify(message=f"runid {runid} not found"), 404

    return jsonify(trace)


@bp.route("/api/run/<string:portal_runid>/trace")
def trace(portal_runid):
    trace = get_trace({'portal_runid': portal_runid})
    if trace is None:
        return jsonify(message=f"portal_runid {portal_runid} not found"), 404

    return jsonify(trace)


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

    if e.get('eventtype') == "IPS_START":
        runid = runs_count()
        run_dict = {key: e[key] for key in run_keys if key in e}
        run_dict['runid'] = runid
        run_dict['events'] = [e]
        run_dict['traces'] = []
        run_dict['has_trace'] = False
        run_dict['monitor_files'] = []
        try:
            add_run(run_dict)
        except pymongo.errors.DuplicateKeyError:
            return jsonify(message="Duplicate portal_runid Key"), 400
        return jsonify(message="New run created", runid=runid)

    msg = "Event added to run"

    update = {"$push": {"events": e}}

    if e.get('eventtype') == "IPS_END":
        run_dict = {key: e[key] for key in run_keys if key in e}
        update["$set"] = run_dict
        msg = "Event added to run and run ended"

    if trace := e.pop('trace', False):
        update["$push"]["traces"] = trace
        if "$set" in update:
            update["$set"]["has_trace"] = True
        else:
            update["$set"] = {"has_trace": True}

    if e.get('eventtype') == "MONITOR_FILE":
        update["$push"]["monitor_files"] = e['comment']

    if update_run({'portal_runid': e.get('portal_runid'), "state": "Running"}, update).modified_count == 0:
        return jsonify(message='Invalid portal_runid'), 400

    return jsonify(message=msg)
