import time
from typing import Tuple, Dict, Any, Optional
from flask import Blueprint, jsonify, request, Response
import pymongo
from ipsportal.db import get_runs, runs_count, get_events, get_run, get_trace, add_run, update_run

bp = Blueprint('api', __name__)


@bp.route("/api/runs")
def runs() -> Tuple[Response, int]:
    return jsonify(get_runs()), 200


@bp.route("/api/run/<int:runid>/events")
def events_runid(runid: int) -> Tuple[Response, int]:
    events = get_events({'runid': runid})
    if events is None:
        return jsonify(message=f"runid {runid} not found"), 404

    return jsonify(events), 200


@bp.route("/api/run/<int:runid>")
def run_runid(runid: int) -> Tuple[Response, int]:
    run = get_run({'runid': runid})
    if run is None:
        return jsonify(message=f"runid {runid} not found"), 404
    return jsonify(run), 200


@bp.route("/api/run/<string:portal_runid>")
def run(portal_runid: str) -> Tuple[Response, int]:
    run = get_run({'portal_runid': portal_runid})
    if run is None:
        return jsonify(message=f"portal_runid {portal_runid} not found"), 404
    return jsonify(run), 200


@bp.route("/api/run/<string:portal_runid>/events")
def events(portal_runid: str) -> Tuple[Response, int]:
    events = get_events({'portal_runid': portal_runid})
    if events is None:
        return jsonify(message=f"portal_runid {portal_runid} not found"), 404
    return jsonify(events), 200


@bp.route("/api/run/<int:runid>/trace")
def trace_runid(runid: int) -> Tuple[Response, int]:
    trace = get_trace({'runid': runid})
    if trace is None:
        return jsonify(message=f"runid {runid} not found"), 404

    return jsonify(trace), 200


@bp.route("/api/run/<string:portal_runid>/trace")
def trace(portal_runid: str) -> Tuple[Response, int]:
    trace = get_trace({'portal_runid': portal_runid})
    if trace is None:
        return jsonify(message=f"portal_runid {portal_runid} not found"), 404

    return jsonify(trace), 200


@bp.route("/", methods=['POST'])
@bp.route("/api/event", methods=['POST'])
def event() -> Tuple[Response, int]:
    e: Optional[Dict[str, Any]] = request.get_json()  # type: ignore[attr-defined]

    if e is None:
        return jsonify(message="Missing data"), 400

    required = {'code', 'eventtype', 'comment', 'walltime', 'phystimestamp', 'portal_runid', 'seqnum'}
    run_keys = {'user', 'host', 'state', 'rcomment', 'tokamak', 'shotno', 'simname', 'startat',
                'stopat', 'sim_runid', 'outputprefix', 'tag', 'ips_version', 'portal_runid', 'ok'}

    if not e.keys() >= required:
        return jsonify(message=f'Missing required data: {sorted(k for k in required if k not in e.keys())}'), 400

    e['created'] = time.strftime('%Y-%m-%d|%H:%M:%S%Z', time.localtime())

    if e.get('eventtype') == "IPS_START":
        runid = runs_count()
        run_dict: Dict[str, Any] = {key: e[key] for key in run_keys if key in e}
        run_dict['runid'] = runid
        run_dict['events'] = [e]
        run_dict['traces'] = []
        run_dict['has_trace'] = False
        run_dict['walltime'] = None
        try:
            add_run(run_dict)
        except pymongo.errors.DuplicateKeyError:
            return jsonify(message="Duplicate portal_runid Key"), 400
        return jsonify(message="New run created", runid=runid), 200

    msg = "Event added to run"

    update: Dict[str, Any] = {"$push": {"events": e}}

    if e.get('eventtype') == "IPS_END":
        run_dict = {key: e[key] for key in run_keys if key in e}
        try:
            run_dict['walltime'] = e['walltime']
        except KeyError:
            pass
        update["$set"] = run_dict
        msg = "Event added to run and run ended"

    if trace := e.pop('trace', False):
        update["$push"]["traces"] = trace
        if "$set" in update:
            update["$set"]["has_trace"] = True
        else:
            update["$set"] = {"has_trace": True}

    if update_run({'portal_runid': e.get('portal_runid'), "state": "Running"}, update).modified_count == 0:
        return jsonify(message='Invalid portal_runid'), 400

    return jsonify(message=msg), 200
