import json
import time
import pymongo
import math
import hashlib
import requests
import numpy as np
import plotly.graph_objects as go
from flask import Blueprint, render_template, request, redirect, url_for
from ipsportal.db import get_db

bp = Blueprint('index', __name__)

ROWS_PER_PAGE = 20
SORT_BY_DEFAULT = 'runid'
SORT_DIRECTION_DEFAULT = -1
SORTABLE = ('runid', 'state', 'rcomment', 'simname', 'host', 'user')
INDEX_COLUMNS = ({'name': 'RunID', 'param': 'runid'},
                 {'name': 'Status', 'param': 'state'},
                 {'name': 'Comment', 'param': 'rcomment'},
                 {'name': 'Sim Name', 'param': 'simname'},
                 {'name': 'Host', 'param': 'host'},
                 {'name': 'User', 'param': 'user'},
                 {'name': 'Start Time', 'param': 'startat'},
                 {'name': 'Stop Time', 'param': 'stopat'})


@bp.route("/")
def index():
    db = get_db()
    page = {}
    page['page'] = request.args.get('page', 1, type=int)
    page['rows'] = request.args.get('rows', ROWS_PER_PAGE, type=int)
    page['rows'] = max(page['rows'], 5)
    page['rows_default'] = ROWS_PER_PAGE
    page['num_pages'] = math.ceil(db.run.estimated_document_count() / page['rows'])
    page['page'] = min(page['page'], page['num_pages'])

    sort = {}
    sort['by'] = request.args.get('sort', SORT_BY_DEFAULT)
    sort['default'] = SORT_BY_DEFAULT
    if sort['by'] not in SORTABLE:
        sort['by'] = SORT_BY_DEFAULT
    sort['direction'] = request.args.get('direction', SORT_DIRECTION_DEFAULT, type=int)
    sort['direction_default'] = SORT_DIRECTION_DEFAULT
    if sort['direction'] not in (1, -1):
        sort['direction'] = SORT_DIRECTION_DEFAULT
    sort['sortable'] = SORTABLE

    runs = db.run.find(skip=max((page['page']-1)*page['rows'], 0),
                       limit=page['rows']
                       ).sort(sort['by'], sort['direction'])
    return render_template("index.html", columns=INDEX_COLUMNS, runs=runs, page=page, sort=sort)


@bp.route("/<int:runid>")
def run(runid):
    db = get_db()
    r = db.run.find_one({'runid': runid})
    if r is None:
        return render_template("notfound.html", run=runid)

    events = db.event.find({'portal_runid': r['portal_runid']}).sort('seqnum', pymongo.DESCENDING)

    return render_template("events.html", run=r, events=events)


@bp.route("/", methods=("POST", "GET"))
def event():
    e = json.loads(request.data)

    required = {'code', 'eventtype', 'comment', 'walltime', 'phystimestamp', 'portal_runid', 'seqnum'}
    if not e.keys() >= required:
        return ('failed', 400)

    e['created'] = time.strftime('%Y-%m-%d|%H:%M:%S%Z', time.localtime())

    db = get_db()

    if e.get('eventtype') == "IPS_START":
        e['runid'] = db.run.estimated_document_count()
        db.run.insert_one(e)
    elif e.get('eventtype') == "IPS_END":
        db.run.update_one({'portal_runid': e.get('portal_runid')}, {'$set': e})

    db.event.insert_one(e)

    return ('success', 200)


@bp.route("/gettrace/<int:runid>")
def gettrace(runid):
    db = get_db()
    r = db.run.find_one({'runid': runid})
    if r is None:
        return render_template("notfound.html", run=runid)

    portal_runid = r['portal_runid']
    traceID = hashlib.md5(portal_runid.encode()).hexdigest()

    x = requests.get(f"http://jaeger:16686/jaeger/api/traces/{traceID}")

    if x.status_code != 200:
        events = db.event.find({'portal_runid': r['portal_runid']})

        spans = [e['trace'] for e in events if 'trace' in e]

        url = 'http://jaeger:9411/api/v2/spans'
        headers = {'accept': 'application/json',
                   'Content-Type': 'application/json'}

        x = requests.post(url, data=json.dumps(spans), headers=headers)

    return redirect(f"/jaeger/trace/{hashlib.md5(r['portal_runid'].encode()).hexdigest()}")


@bp.route("/resource_plot/<int:runid>")
def resource_plot(runid):
    db = get_db()
    r = db.run.find_one({'runid': runid})
    if r is None:
        return render_template("notfound.html", run=runid)

    events = db.event.find({'portal_runid': r['portal_runid']})

    tasks = []
    task_set = set()

    for ev in events:
        if ev["eventtype"] == "IPS_TASK_END":
            tasks.append(ev)
            task_set.add(ev['trace']['localEndpoint']['serviceName'])

    time_start = float(r["trace"]['timestamp'])/1e6
    duration = float(r["trace"]['duration'])/1e6
    total_cores = int(r["trace"]['tags']['total_cores'])

    task_plots = {'x': []}
    for task in task_set:
        task_plots[task] = []

    task_plots['x'].append(0)
    task_plots['x'].append(duration)
    for task in task_set:
        task_plots[task].append(0.)
        task_plots[task].append(0.)

    for t in tasks:
        start = float(t['trace']['timestamp'])/1e6 - time_start
        end = float(t['trace']['timestamp'] + t['trace']['duration'])/1e6 - time_start
        name = t['trace']['localEndpoint']['serviceName']
        task_plots['x'].append(start-1e-9)
        task_plots['x'].append(start)
        task_plots['x'].append(end-1.e-9)
        task_plots['x'].append(end)
        cores = float(t['trace']['tags']['cores_allocated'])
        for task in task_set:
            if task == name:
                task_plots[task].append(0.)
                task_plots[task].append(cores)
                task_plots[task].append(0.)
                task_plots[task].append(-cores)
            else:
                task_plots[task].append(0.)
                task_plots[task].append(0.)
                task_plots[task].append(0.)
                task_plots[task].append(0.)

    x = task_plots['x']
    sort_idx = np.argsort(x)

    plot = go.Figure()
    for task, y in task_plots.items():
        if task == 'x':
            continue
        plot.add_trace(go.Scatter(
            name=task,
            x=np.asarray(x)[sort_idx],
            y=np.cumsum(np.asarray(y)[sort_idx]),
            stackgroup='one'
        ))

    plot.update_xaxes(title="Walltime (s)")
    plot.update_yaxes(title="Cores allocated",
                      range=(0, total_cores))
    link = url_for('.run', runid=runid)
    plot.update_layout(title=f"<a href='{link}'>Run - {runid}</a> "
                       f"Sim Name: {r['sim_name']} Comment: {r['rcomment']}<br>"
                       f"Allocation total cores = {total_cores}",
                       legend_title_text="Tasks")
    return plot.to_html()
