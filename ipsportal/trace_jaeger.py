import hashlib
from typing import Any

import requests
from flask import Blueprint, current_app, redirect, url_for
from werkzeug.wrappers import Response

from ipsportal.db import get_portal_runid, get_trace

from .environment import JAEGER_HOST

bp = Blueprint('trace', __name__)


@bp.route('/gettrace/<int:runid>')
def gettrace(runid: int) -> tuple[str, int] | Response:
    portal_runid = get_portal_runid(runid)
    traceID = hashlib.md5(portal_runid.encode()).hexdigest()

    try:
        x = requests.get(f'http://{JAEGER_HOST}:16686/jaeger/api/traces/{traceID}', timeout=60)
    except requests.exceptions.ConnectionError:
        current_app.logger.exception('Unable to connect to jaeger')
        return 'Unable to connect to jaeger', 500

    if x.status_code != 200:
        trace = get_trace({'runid': runid})
        if trace is None:
            return 'No trace available', 500

        try:
            response = send_trace(trace)
        except requests.exceptions.ConnectionError:
            current_app.logger.exception('Unable to create trace')
            return 'Unable to create trace', 500

        if response.status_code != 202:
            return f'Failed sending trace with {response.status_code}', 500

    return redirect(url_for('trace.jaeger', trace=f'trace/{traceID}'))


@bp.route('/jaeger/<path:trace>')
def jaeger(trace: str) -> Response:
    if trace.startswith('trace/') and trace[6:].isalnum() and len(trace) == 38:
        return redirect(f'http://{JAEGER_HOST}:16686/jaeger/{trace}')
    return Response('Unable to get trace', 500)


def send_trace(trace: list[dict[str, Any]]) -> requests.Response:
    url = f'http://{JAEGER_HOST}:9411/api/v2/spans'
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}

    return requests.post(url, json=trace, headers=headers, timeout=1)
