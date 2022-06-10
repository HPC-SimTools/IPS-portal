from flask import Blueprint, render_template
from ipsportal.db import get_run, get_datafiles

bp = Blueprint('index', __name__)

INDEX_COLUMNS = ({'name': 'RunID', 'param': 'runid'},
                 {'name': 'Status', 'param': 'state'},
                 {'name': 'Comment', 'param': 'rcomment'},
                 {'name': 'Sim Name', 'param': 'simname'},
                 {'name': 'Host', 'param': 'host'},
                 {'name': 'User', 'param': 'user'},
                 {'name': 'Start Time', 'param': 'startat'},
                 {'name': 'Stop Time', 'param': 'stopat'},
                 {'name': 'Walltime', 'param': 'walltime'})


@bp.route("/")
def index():
    return render_template("index.html", columns=INDEX_COLUMNS)


@bp.route("/<int:runid>")
def run(runid: int):
    run = get_run({'runid': runid})
    if run is None:
        return render_template("notfound.html", run=runid), 404
    datafiles = get_datafiles({'runid': runid})
    return render_template("events.html", run=run, datafiles=datafiles)
