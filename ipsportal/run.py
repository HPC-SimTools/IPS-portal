from typing import Tuple
from flask import Blueprint, render_template
from ipsportal.db import get_run, get_runid

bp = Blueprint('index', __name__)


@bp.route("/")
def index() -> Tuple[str, int]:
    return render_template("index.html"), 200


@bp.route("/<int:runid>")
def run(runid: int) -> Tuple[str, int]:
    run = get_run({'runid': runid})
    if run is None:
        return render_template("notfound.html", run=runid), 404

    if run.get('parent_portal_runid') is not None:
        run['parent_runid'] = get_runid(str(run.get('parent_portal_runid')))
    else:
        run['parent_runid'] = None
    return render_template("events.html", run=run), 200
