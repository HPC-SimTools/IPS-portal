import os
import hashlib
import requests
from typing import Tuple, Union, List, Any, Dict
from flask import Blueprint, redirect, url_for, current_app
from werkzeug.wrappers import Response
from ipsportal.db import get_trace, get_portal_runid

bp = Blueprint('trace', __name__)

JAEGER_HOSTNAME = os.environ.get('JAEGER_HOST', 'localhost')


@bp.route("/gettrace/<int:runid>")
def gettrace(runid: int) -> Union[Tuple[str, int], Response]:
    portal_runid = get_portal_runid(runid)
    traceID = hashlib.md5(portal_runid.encode()).hexdigest()

    try:
        x = requests.get(f"http://{JAEGER_HOSTNAME}:16686/jaeger/api/traces/{traceID}")
    except requests.exceptions.ConnectionError as e:
        current_app.logger.error(f"Unable to connect to jaeger because:<br>{e}")
        return "Unable to connect to jaeger", 500

    if x.status_code != 200:
        trace = get_trace({"runid": runid})
        if trace is None:
            return "No trace available", 500

        try:
            response = send_trace(trace)
        except requests.exceptions.ConnectionError as e:
            current_app.logger.error(f"Unable to create trace because:<br>{e}")
            return "Unable to create trace", 500

        if response.status_code != 202:
            return f"Failed sending trace with {response.status_code}", 500

    return redirect(url_for("trace.jaeger", trace=f"trace/{traceID}"))


@bp.route("/jaeger/<path:trace>")
def jaeger(trace: str) -> Response:
    if trace.startswith("trace/") and trace[6:].isalnum() and len(trace) == 38:
        return redirect(f"http://{JAEGER_HOSTNAME}:16686/jaeger/{trace}")
    return Response("Unable to get trace", 500)


def send_trace(trace: List[Dict[str, Any]]) -> requests.Response:
    url = f'http://{JAEGER_HOSTNAME}:9411/api/v2/spans'
    headers = {'accept': 'application/json',
               'Content-Type': 'application/json'}

    return requests.post(url, json=trace, headers=headers, timeout=1)
