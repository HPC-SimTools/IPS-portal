import json
import time
import pymongo
from flask import Blueprint, render_template, request
from ipsportal.db import get_db

bp = Blueprint('index', __name__)


@bp.route("/")
def index():
    db = get_db()
    runs = db.run.find().sort('id', pymongo.DESCENDING)
    return render_template("index.html", runs=runs)


@bp.route("/<int:id>")
def run(id):
    db = get_db()
    r = db.run.find_one({'id': id})
    if r is None:
        return render_template("notfound.html", run=id)

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
        e['id'] = db.run.estimated_document_count()
        db.run.insert_one(e)
    elif e.get('eventtype') == "IPS_END":
        db.run.update_one({'portal_runid': e.get('portal_runid')}, {'$set': e})

    db.event.insert_one(e)

    return ('success', 200)
