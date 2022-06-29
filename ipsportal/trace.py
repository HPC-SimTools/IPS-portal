import os
import hashlib
import requests
from typing import Tuple, Union
from flask import Blueprint, redirect, url_for
from werkzeug.wrappers import Response
from ipsportal.db import get_trace, get_run

bp = Blueprint('trace', __name__)

JAEGER_HOSTNAME = os.environ.get('JAEGER_HOST', 'localhost')


@bp.route("/gettrace/<int:runid>")
def gettrace(runid: int) -> Union[Tuple[str, int], Response]:
    run = get_run({"runid": runid})

    portal_runid = run['portal_runid']
    traceID = hashlib.md5(portal_runid.encode()).hexdigest()

    try:
        x = requests.get(f"http://{JAEGER_HOSTNAME}:16686/jaeger/api/traces/{traceID}")
    except requests.exceptions.ConnectionError as e:
        return f"Unable to connect to jaeger because:<br>{e}", 500

    if x.status_code != 200:
        trace = get_trace({"runid": runid})

        url = f'http://{JAEGER_HOSTNAME}:9411/api/v2/spans'
        headers = {'accept': 'application/json',
                   'Content-Type': 'application/json'}

        try:
            x = requests.post(url, json=trace, headers=headers, timeout=1)
        except requests.exceptions.ConnectionError as e:
            return f"Unable to create trace because:<br>{e}", 500

    return redirect(url_for("trace.jaeger", trace=f"trace/{traceID}"))


@bp.route("/jaeger/<path:trace>")
def jaeger(trace: str) -> Response:
    return redirect(f"http://{JAEGER_HOSTNAME}:16686/jaeger/{trace}")
