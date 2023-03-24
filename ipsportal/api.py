import time
from typing import Tuple, Dict, Any, Optional, List, Union
from flask import Blueprint, jsonify, request, Response, current_app
import pymongo
import requests
import hashlib
from ipsportal.db import (get_runs, get_events, get_run, next_runid,
                          get_trace, add_run, update_run, get_portal_runid,
                          get_parent_portal_runid)
from ipsportal.trace import send_trace

bp = Blueprint('api', __name__)


@bp.route("/api/runs")
def runs() -> Tuple[Response, int]:
    return jsonify(get_runs(filter={'parent_portal_runid': None})), 200


@bp.route("/api/run/<string:portal_runid>/children")
def child_runs(portal_runid: str) -> Tuple[Response, int]:
    return jsonify(get_runs(filter={'parent_portal_runid': portal_runid})), 200


@bp.route("/api/run/<int:runid>/children")
def child_runs_runid(runid: int) -> Tuple[Response, int]:
    return jsonify(get_runs(filter={'parent_portal_runid': get_portal_runid(runid)})), 200


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
    if trace == []:
        return jsonify(message=f"runid {runid} not found"), 404

    return jsonify(trace), 200


@bp.route("/api/run/<string:portal_runid>/trace")
def trace(portal_runid: str) -> Tuple[Response, int]:
    trace = get_trace({'portal_runid': portal_runid})
    if trace == []:
        return jsonify(message=f"portal_runid {portal_runid} not found"), 404

    return jsonify(trace), 200


@bp.route("/", methods=['POST'])
@bp.route("/api/event", methods=['POST'])
def event() -> Tuple[Response, int]:
    event_list: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = request.get_json()  # type: ignore[attr-defined]

    if event_list is None:
        current_app.logger.error("Missing data")
        return jsonify(message="Missing data"), 400

    successes = 0
    errors = []

    if isinstance(event_list, dict):
        event_list = [event_list]

    output: Dict[str, Any] = {}
    output['message'] = "{} events added to run"

    for e in event_list:

        required = {'code', 'eventtype', 'comment', 'walltime', 'phystimestamp', 'portal_runid', 'seqnum'}
        run_keys = {'user', 'host', 'state', 'rcomment', 'tokamak', 'shotno', 'simname', 'startat',
                    'stopat', 'sim_runid', 'outputprefix', 'tag', 'ips_version', 'portal_runid', 'ok', 'walltime',
                    'parent_portal_runid', 'vizurl'}

        if not e.keys() >= required:
            current_app.logger.error(f"Missing required data: {e}")
            return jsonify(message=f'Missing required data: {sorted(k for k in required if k not in e.keys())}'), 400

        if 'time' not in e:
            e['time'] = time.strftime('%Y-%m-%d|%H:%M:%S%Z', time.localtime())

        if e.get('eventtype') == "IPS_START":
            runid = next_runid()
            run_dict: Dict[str, Any] = {key: e[key] for key in run_keys if key in e}
            run_dict['runid'] = runid
            run_dict['events'] = [e]
            run_dict['traces'] = []
            run_dict['has_trace'] = False
            try:
                add_run(run_dict)
            except pymongo.errors.DuplicateKeyError:
                current_app.logger.error(f"Duplicate Key {run_dict}")
                errors.append("Duplicate portal_runid Key")
                continue
            successes += 1
            output['message'] = "New run created and " + output['message']
            output['runid'] = runid
            continue

        update: Dict[str, Any] = {"$push": {"events": e}}
        update["$currentDate"] = {
            "lastModified": True,
        }

        if e.get('eventtype') == "IPS_END":
            run_dict = {key: e[key] for key in run_keys if key in e}
            update["$set"] = run_dict
            output['message'] = output['message'] + " and run ended"
        else:
            update["$set"] = {'walltime': e.get('walltime')}
            if 'vizurl' in e:
                update["$set"]['vizurl'] = e.get('vizurl')

        if trace := e.pop('trace', False):
            update["$push"]["traces"] = trace
            if "$set" in update:
                update["$set"]["has_trace"] = True
            else:
                update["$set"] = {"has_trace": True}

        update_result = update_run({'portal_runid': e.get('portal_runid'), "state": "Running"}, update)
        if update_result.modified_count == 0:
            current_app.logger.error(f"Invalid portal_runid {update}")
            errors.append('Invalid portal_runid')
            continue

        if trace:
            traces = [trace]

            # add traces to parent run recursively
            portal_runid = e['portal_runid']
            while parent_portal_runid := get_parent_portal_runid(portal_runid):
                new_trace = trace.copy()
                new_trace['traceId'] = hashlib.md5(parent_portal_runid.encode()).hexdigest()
                traces.append(new_trace)
                portal_runid = parent_portal_runid

            try:
                send_trace(traces)
            except requests.exceptions.ConnectionError:
                pass

        successes += 1

    output['message'] = output['message'].format(successes)

    if errors:
        return jsonify(**output, errors=errors), 400

    return jsonify(**output), 200


@bp.route("/api/version")
def version() -> Tuple[Response, int]:
    from importlib.metadata import version
    return jsonify(version=version("ipsportal")), 200
