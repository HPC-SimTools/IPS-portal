from typing import Any

import plotly.graph_objects as go
from flask import Blueprint, current_app, url_for

from ipsportal.db import get_run, get_trace

bp = Blueprint('resourceplot', __name__)


@bp.route('/resource_plot/<int:runid>')
def resource_plot(runid: int) -> tuple[str, int]:
    traces = get_trace({'runid': runid})
    if traces is None:
        return 'Unable to plot because missing trace information', 500

    # last trace should get the IPS_END event
    try:
        total_cores = traces[-1]['tags']['total_cores']
        time_start = float(traces[-1]['timestamp']) / 1e6
        duration = float(traces[-1]['duration']) / 1e6
    except KeyError:
        current_app.logger.exception('Unable to plot because missing %s information')
        return 'Unable to plot because missing information', 500

    run = get_run({'runid': runid})
    if run is None:
        return 'Missing run', 404

    tasks = []
    task_set = set()
    try:
        for trace in traces:
            if 'tags' in trace and 'cores_allocated' in trace['tags']:
                tasks.append(trace)
                task_set.add(trace['localEndpoint']['serviceName'])

        task_plots: dict[str, Any] = {'x': []}
        for task in task_set:
            task_plots[task] = []

        task_plots['x'].append(0)
        task_plots['x'].append(duration)
        for task in task_set:
            task_plots[task].append(0.0)
            task_plots[task].append(0.0)

        for t in tasks:
            start = float(t['timestamp']) / 1e6 - time_start
            end = float(t['timestamp'] + t['duration']) / 1e6 - time_start
            name = t['localEndpoint']['serviceName']
            task_plots['x'].append(start - 1e-9)
            task_plots['x'].append(start)
            task_plots['x'].append(end - 1.0e-9)
            task_plots['x'].append(end)
            cores = float(t['tags']['cores_allocated'])
            for task in task_set:
                if task == name:
                    task_plots[task].append(0.0)
                    task_plots[task].append(cores)
                    task_plots[task].append(0.0)
                    task_plots[task].append(-cores)
                else:
                    task_plots[task].append(0.0)
                    task_plots[task].append(0.0)
                    task_plots[task].append(0.0)
                    task_plots[task].append(0.0)
    except KeyError:
        current_app.logger.exception('Unable to plot because missing information')
        return 'Unable to plot because missing information', 500

    plot = go.Figure()
    for task in task_set:
        # sort x and y arrays by x
        x, y = list(zip(*sorted(zip(task_plots['x'], task_plots[task], strict=False)), strict=False))

        plot.add_trace(
            go.Scatter(
                name=task,
                x=x,
                y=[sum(y[: n + 1]) for n in range(len(y))],  # cumsum
                stackgroup='one',
            )
        )

    plot.update_xaxes(title='Walltime (s)')
    plot.update_yaxes(title='Cores allocated', range=(0, total_cores))
    link = url_for('index.run', runid=runid)
    plot.update_layout(
        title=f"<a href='{link}'>Run - {runid}</a> "
        f'Sim Name: {run["simname"]} Comment: {run["rcomment"]}<br>'
        f'Allocation total cores = {total_cores}',
        legend_title_text='Tasks',
    )
    return plot.to_html(), 200
