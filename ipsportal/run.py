import json
from flask import Blueprint, render_template, request
from ipsportal.db import get_db

bp = Blueprint('index', __name__)


@bp.route("/")
def index():
    db = get_db()
    runs = db.execute("SELECT * FROM run ORDER BY id DESC").fetchall()
    return render_template("index.html", runs=runs)


@bp.route("/<int:id>")
def run(id):
    db = get_db()
    r = db.execute('SELECT * FROM run WHERE id=?', (str(id),)).fetchone()
    if r is None:
        return ("Run ID {0} does not exist.".format(id), 404)
    portal_runid = r['portal_runid']
    events = db.execute("SELECT * FROM event WHERE portal_runid=? ORDER BY seqnum DESC", (portal_runid,)).fetchall()
    return render_template("events.html", run=r, events=events)


@bp.route("/", methods=("POST", "GET"))
def event():
    e = json.loads(request.data)
    required = {'code', 'eventtype', 'comment', 'walltime', 'phystimestamp', 'portal_runid', 'seqnum'}
    if not e.keys() >= required:
        return ('failed', 400)
    db = get_db()
    if e.get('eventtype') == "IPS_START":
        db.execute("INSERT INTO run (portal_runid, state, rcomment, tokamak, shotno, simname, host, user, startat, simrunid, outputprefix, tag, simroot) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (e.get('portal_runid'),
                    e.get('state'),
                    e.get('rcomment'),
                    e.get('tokamak'),
                    e.get('shotno'),
                    e.get('simname'),
                    e.get('host'),
                    e.get('user'),
                    e.get('startat'),
                    e.get('simrunid'),
                    e.get('outputprefix'),
                    e.get('tag'),
                    e.get('simroot')))
    elif e.get('eventtype') == "IPS_END":
        db.execute("UPDATE run SET state = ?, stopat = ? WHERE portal_runid = ?", (e.get('state'), e.get('stopat'), e.get('portal_runid')))
    db.execute("INSERT INTO event (code, eventtype, comment, walltime, phystimestamp, portal_runid, seqnum) VALUES (?,?,?,?,?,?,?)",
               (e.get('code'),
                e.get('eventtype'),
                e.get('comment'),
                e.get('walltime'),
                e.get('phystimestamp'),
                e.get('portal_runid'),
                e.get('seqnum')))
    db.commit()

    return ('success', 200)
