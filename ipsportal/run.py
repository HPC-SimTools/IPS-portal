from flask import Blueprint, render_template
from ipsportal.db import get_db

bp = Blueprint('index', __name__)


@bp.route("/")
def index():
    db = get_db()
    runs = db.execute("SELECT * FROM run").fetchall()
    return render_template("index.html", runs=runs)

@bp.route("/run/<int:id>")
def run(id):
    db = get_db()
    run = db.execute('SELECT * FROM run WHERE id=?', str(id)).fetchone()
    if run is None:
        return "Run id {0} doesn't exist.".format(id)
    portal_runid = run['portal_runid']
    events = db.execute("SELECT * FROM event WHERE portal_runid=?", (portal_runid,)).fetchall()
    return render_template("events.html", events=events)
