import hashlib
import logging
import time
from json import JSONDecodeError
from typing import Any

import pymongo
import pymongo.errors
import requests
from flask import Blueprint, Response, current_app, json, jsonify, request

from ipsportal.datatables import get_datatables_results
from ipsportal.db import (
    add_run,
    get_ensembles,
    get_events,
    get_parent_portal_runid,
    get_portal_runid,
    get_run,
    get_runid,
    get_runs,
    get_runs_total,
    get_trace,
    next_runid,
    update_run,
)
from ipsportal.ensemble import update_ensemble_information

# from ipsportal.environment import SECRET_API_KEY
from ipsportal.trace_jaeger import send_trace
from ipsportal.util import ALLOWED_PROPS_RUN

logger = logging.getLogger(__name__)

bp = Blueprint('api', __name__)


@bp.route('/api/runs-datatables')
def runs_datatables() -> tuple[Response, int]:
    try:
        arguments: dict[str, Any] = json.loads(request.args.get('data', '{}'))
    except JSONDecodeError:
        return jsonify(('data', '"data" query parameter must be JSON-parseable')), 400

    try:
        datatables_ok, datatables_value = get_datatables_results(
            arguments,
            allowed_props=ALLOWED_PROPS_RUN,
            data_query_fn=get_runs,
            count_query_fn=get_runs_total,
            base_filter={'parent_portal_runid': None},
        )
    except pymongo.errors.PyMongoError:
        logger.exception('Pymongo error')
        return jsonify('Internal Service Error'), 500
    if not datatables_ok:
        logger.warning('DataTables value invalid: %s', datatables_value)
        return jsonify(datatables_value), 400
    return jsonify(datatables_value), 200


# TODO - legacy, consider removing once tests are reworked.
@bp.route('/api/runs')
def runs() -> tuple[Response, int]:
    try:
        return jsonify(get_runs(db_filter={'parent_portal_runid': None}, limit=100)), 200
    except pymongo.errors.PyMongoError:
        logger.exception('Pymongo error')
        return jsonify('Interal Service Error'), 500


@bp.route('/api/run/<string:portal_runid>/children')
def child_runs(portal_runid: str) -> tuple[Response, int]:
    return jsonify(get_runs(db_filter={'parent_portal_runid': portal_runid})), 200


@bp.route('/api/run/<int:runid>/children')
def child_runs_runid(runid: int) -> tuple[Response, int]:
    return jsonify(get_runs(db_filter={'parent_portal_runid': get_portal_runid(runid)})), 200


@bp.route('/api/run/<int:runid>/events')
def events_runid(runid: int) -> tuple[Response, int]:
    events = get_events({'runid': runid})
    if events is None:
        return jsonify(message=f'runid {runid} not found'), 404

    return jsonify(events), 200


@bp.route('/api/run/<int:runid>')
def run_runid(runid: int) -> tuple[Response, int]:
    run = get_run({'runid': runid})
    if run is None:
        return jsonify(message=f'runid {runid} not found'), 404
    return jsonify(run), 200


@bp.route('/api/run/<string:portal_runid>')
def run(portal_runid: str) -> tuple[Response, int]:
    run = get_run({'portal_runid': portal_runid})
    if run is None:
        return jsonify(message=f'portal_runid {portal_runid} not found'), 404
    return jsonify(run), 200


@bp.route('/api/run/<string:portal_runid>/events')
def events(portal_runid: str) -> tuple[Response, int]:
    events = get_events({'portal_runid': portal_runid})
    if events is None:
        return jsonify(message=f'portal_runid {portal_runid} not found'), 404
    return jsonify(events), 200


@bp.route('/api/run/<int:runid>/trace')
def trace_runid(runid: int) -> tuple[Response, int]:
    trace = get_trace({'runid': runid})
    if trace == []:
        return jsonify(message=f'runid {runid} not found'), 404

    return jsonify(trace), 200


@bp.route('/api/run/<string:portal_runid>/trace')
def trace(portal_runid: str) -> tuple[Response, int]:
    trace = get_trace({'portal_runid': portal_runid})
    if trace == []:
        return jsonify(message=f'portal_runid {portal_runid} not found'), 404

    return jsonify(trace), 200


@bp.route('/', methods=['POST'])
@bp.route('/api/event', methods=['POST'])
def event() -> tuple[Response, int]:
    # api_key = request.headers.get("X-Api-Key")
    # if api_key != SECRET_API_KEY:
    # return jsonify(message="Authorization failed"), 401

    event_list: list[dict[str, Any]] | dict[str, Any] | None = request.get_json()  # type: ignore[attr-defined]

    if event_list is None:
        current_app.logger.error('Missing data')
        return jsonify(message='Missing data'), 400

    successes = 0
    errors = []

    if isinstance(event_list, dict):
        event_list = [event_list]

    output: dict[str, Any] = {}
    output['message'] = '{} events added to run'

    for e in event_list:
        required = {'code', 'eventtype', 'comment', 'walltime', 'phystimestamp', 'portal_runid', 'seqnum'}
        run_keys = {
            'user',
            'host',
            'state',
            'rcomment',
            'tokamak',
            'shotno',
            'simname',
            'startat',
            'stopat',
            'sim_runid',
            'outputprefix',
            'tag',
            'ips_version',
            'portal_runid',
            'ok',
            'walltime',
            'parent_portal_runid',
            'portal_ensemble_id',
            'vizurl',
        }

        if not e.keys() >= required:
            current_app.logger.error('Missing required data: %s', e)
            return jsonify(message=f'Missing required data: {sorted(k for k in required if k not in e)}'), 400

        if 'time' not in e:
            e['time'] = time.strftime('%Y-%m-%d|%H:%M:%S%Z', time.localtime())

        if e.get('eventtype') == 'IPS_START':
            runid = next_runid()
            run_dict: dict[str, Any] = {key: e[key] for key in run_keys if key in e}
            run_dict['runid'] = runid
            run_dict['events'] = [e]
            run_dict['traces'] = []
            run_dict['has_trace'] = False
            try:
                add_run(run_dict)
                # if this is an ensemble run, we need to update its parent
                if (
                    'portal_ensemble_id' in run_dict
                    and 'parent_portal_runid' in run_dict
                    and 'simname' in run_dict
                    and 'user' in run_dict
                ):
                    logger.info(
                        'Preparing to update ensemble CSV with runid %s of parent_portal_runid %s',
                        runid,
                        run_dict['parent_portal_runid'],
                    )
                    error = ''
                    parent_integer_runid = get_runid(run_dict['parent_portal_runid'])
                    if parent_integer_runid is not None:
                        ensembles = get_ensembles(parent_integer_runid, run_dict['portal_ensemble_id'])
                        if ensembles is not None:
                            try:
                                update_ensemble_information(
                                    runid,
                                    request.root_url.rstrip('/'),
                                    run_dict['simname'],
                                    run_dict['user'],
                                    ensembles[0]['path'],
                                )
                            except Exception:
                                logger.exception('update_ensemble_information exception...')
                                error = 'exception from update_ensemble_information'
                        else:
                            error = 'failed when trying to get the actual runid from the parent_portal_runid and the portal_ensemble_id'
                    else:
                        error = 'unable to retrieve the real runid from the parent portal runid'
                    if error:
                        errors.append('Could not update parent ensemble information')
                        current_app.logger.error(
                            'Could not update parent ensemble information for parentid=%s simname=%s ensemble_id=%s because: %s',
                            run_dict['parent_portal_runid'],
                            run_dict['simname'],
                            run_dict['portal_ensemble_id'],
                            error,
                        )
            except FileNotFoundError:
                current_app.logger.exception('no file for %s', run_dict['parent_portal_runid'])
                errors.append('could not update ensemble file')
                continue
            except pymongo.errors.DuplicateKeyError:
                current_app.logger.exception('Duplicate Key %s', run_dict)
                errors.append('Duplicate portal_runid Key')
                continue
            except Exception:
                current_app.logger.exception('unknown IPS_START exception')
                continue
            successes += 1
            output['message'] = 'New run created and ' + output['message']
            output['runid'] = runid
            if 'simname' in e:
                output['simname'] = e['simname']
            continue

        update: dict[str, Any] = {'$push': {'events': e}}
        update['$currentDate'] = {
            'lastModified': True,
        }

        if e.get('eventtype') == 'IPS_END':
            run_dict = {key: e[key] for key in run_keys if key in e}
            update['$set'] = run_dict
            output['message'] = output['message'] + ' and run ended'
        else:
            update['$set'] = {'walltime': e.get('walltime')}
            if 'vizurl' in e:
                update['$set']['vizurl'] = e.get('vizurl')

        if trace := e.pop('trace', False):
            update['$push']['traces'] = trace
            if '$set' in update:
                update['$set']['has_trace'] = True
            else:
                update['$set'] = {'has_trace': True}

        update_result = update_run({'portal_runid': e.get('portal_runid'), 'state': 'Running'}, update)
        if update_result.modified_count == 0:
            current_app.logger.error('Invalid portal_runid %s', update)
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


@bp.route('/api/version')
def version() -> tuple[Response, int]:
    from importlib.metadata import version

    return jsonify(version=version('ipsportal')), 200
