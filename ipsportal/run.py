from flask import Blueprint, render_template
from ipsportal.db import get_run

bp = Blueprint('index', __name__)

@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/<int:runid>")
def run(runid: int):
    run = get_run({'runid': runid})
    if run is None:
        return render_template("notfound.html", run=runid), 404
    return render_template("events.html", run=run)
