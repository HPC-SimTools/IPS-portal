import json
import time
import pymongo
import math
from flask import Blueprint, render_template, request
from ipsportal.db import get_db

bp = Blueprint('index', __name__)

ROWS_PER_PAGE = 20


@bp.route("/")
def index():
    db = get_db()
    page = request.args.get('page', 1, type=int)
    num_pages = math.ceil(db.run.estimated_document_count() / ROWS_PER_PAGE)
    pages = range(1, num_pages+1)
    runs = db.run.find(skip=(page-1)*ROWS_PER_PAGE, limit=ROWS_PER_PAGE).sort('runid', pymongo.DESCENDING)
    return render_template("index.html", runs=runs, pages=pages, page=page, num_pages=num_pages)


@bp.route("/<int:runid>")
def run(runid):
    db = get_db()
    r = db.run.find_one({'runid': runid})
    if r is None:
        return render_template("notfound.html", run=runid)

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
        e['runid'] = db.run.estimated_document_count()
        db.run.insert_one(e)
    elif e.get('eventtype') == "IPS_END":
        db.run.update_one({'portal_runid': e.get('portal_runid')}, {'$set': e})

    db.event.insert_one(e)

    return ('success', 200)
