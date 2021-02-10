import json
from flask import Blueprint, render_template, request, jsonify
from ipsportal.db import get_db

bp = Blueprint('index', __name__)


@bp.route("/")
def index():
    db = get_db()
    runs = db.execute("SELECT * FROM run").fetchall()
    return render_template("index.html", runs=runs)


@bp.route("/<int:id>")
def run(id):
    db = get_db()
    r = db.execute('SELECT * FROM run WHERE id=?', str(id)).fetchone()
    if r is None:
        return "Run id {0} doesn't exist.".format(id)
    portal_runid = r['portal_runid']
    events = db.execute("SELECT * FROM event WHERE portal_runid=?", (portal_runid,)).fetchall()
    return render_template("events.html", events=events)


@bp.route("/", methods=("POST", "GET"))
def event():
    e = json.loads(request.data)
    db = get_db()
    if e.get('eventtype') == "IPS_START":
        db.execute("INSERT INTO run (portal_runid, state, rcomment, tokamak, shotno) VALUES (?,?,?,?,?)",
                   (e.get('portal_runid'),
                    e.get('state'),
                    e.get('rcomment'),
                    e.get('tokamak'),
                    e.get('shotno')))

    db.execute("INSERT INTO event (code, eventtype, comment, walltime, phystimestamp, portal_runid, seqnum) VALUES (?,?,?,?,?,?,?)",
               (e.get('code'),
                e.get('eventtype'),
                e.get('comment'),
                e.get('walltime'),
                e.get('phystimestamp'),
                e.get('portal_runid'),
                e.get('seqnum')))
    db.commit()

    return jsonify(e)
