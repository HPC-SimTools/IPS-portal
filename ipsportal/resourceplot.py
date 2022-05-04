import plotly.graph_objects as go
import numpy as np
from flask import Blueprint, render_template, url_for
from ipsportal.db import get_db

bp = Blueprint('resourceplot', __name__)


@bp.route("/resource_plot/<int:runid>")
def resource_plot(runid):
    db = get_db()
    r = db.run.find_one({'runid': runid})
    if r is None:
        return render_template("notfound.html", run=runid)

    events = db.event.find({'portal_runid': r['portal_runid']})

    tasks = []
    task_set = set()

    try:
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
    except KeyError as e:
        return f"Unable to plot because missing {e} information", 500

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
    link = url_for('index.run', runid=runid)
    plot.update_layout(title=f"<a href='{link}'>Run - {runid}</a> "
                       f"Sim Name: {r['sim_name']} Comment: {r['rcomment']}<br>"
                       f"Allocation total cores = {total_cores}",
                       legend_title_text="Tasks")
    return plot.to_html()