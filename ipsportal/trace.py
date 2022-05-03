import os
import hashlib
import requests
from flask import Blueprint, redirect, render_template, url_for
from ipsportal.db import get_db

bp = Blueprint('trace', __name__)

JAEGER_HOSTNAME = os.environ.get('JAEGER_HOSTNAME', 'localhost')


@bp.route("/gettrace/<int:runid>")
def gettrace(runid):
    db = get_db()
    r = db.run.find_one({'runid': runid})
    if r is None:
        return render_template("notfound.html", run=runid)

    portal_runid = r['portal_runid']
    traceID = hashlib.md5(portal_runid.encode()).hexdigest()

    try:
        x = requests.get(f"http://{JAEGER_HOSTNAME}:16686/jaeger/api/traces/{traceID}")
    except requests.exceptions.ConnectionError as e:
        return f"Unable to connect to jaeger because:<br>{e}", 500

    if x.status_code != 200:
        events = db.event.find({'portal_runid': r['portal_runid']})

        spans = [e['trace'] for e in events if 'trace' in e]

        url = f'http://{JAEGER_HOSTNAME}:9411/api/v2/spans'
        headers = {'accept': 'application/json',
                   'Content-Type': 'application/json'}

        try:
            x = requests.post(url, json=spans, headers=headers, timeout=1)
        except requests.exceptions.ConnectionError as e:
            return f"Unable to create trace because:<br>{e}", 500

    return redirect(url_for("trace.jaeger", trace=f"trace/{traceID}"))


@bp.route("/jaeger/<path:trace>")
def jaeger(trace):
    return redirect(f"http://{JAEGER_HOSTNAME}:16686/jaeger/{trace}")
