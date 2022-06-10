from typing import Tuple
from flask import Blueprint, render_template
from ipsportal.db import get_run

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
def index() -> Tuple[str, int]:
    return render_template("index.html", columns=INDEX_COLUMNS), 200


@bp.route("/<int:runid>")
def run(runid: int) -> Tuple[str, int]:
    run = get_run({'runid': runid})
    if run is None:
        return render_template("notfound.html", run=runid), 404
    return render_template("events.html", run=run), 200
