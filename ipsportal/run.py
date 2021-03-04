import json
import time
import pymongo
import math
from flask import Blueprint, render_template, request
from ipsportal.db import get_db

bp = Blueprint('index', __name__)

ROWS_PER_PAGE = 20
SORT_BY_DEFAULT = 'runid'
SORT_DIRECTION_DEFAULT = -1


@bp.route("/")
def index():
    db = get_db()
    page = {}
    page['page'] = request.args.get('page', 1, type=int)
    page['rows'] = request.args.get('rows', ROWS_PER_PAGE, type=int)
    page['rows'] = max(page['rows'], 5)
    page['rows_default'] = ROWS_PER_PAGE
    page['num_pages'] = math.ceil(db.run.estimated_document_count() / page['rows'])
    page['page'] = min(page['page'], page['num_pages'])

    sort = {}
    sort['by'] = request.args.get('sort', SORT_BY_DEFAULT)
    sort['default'] = SORT_BY_DEFAULT
    if sort['by'] not in ('runid', 'state', 'rcomment', 'simname', 'host', 'user'):
        sort['by'] = SORT_BY_DEFAULT
    sort['direction'] = request.args.get('direction', SORT_DIRECTION_DEFAULT, type=int)
    sort['direction_default'] = SORT_DIRECTION_DEFAULT
    if sort['direction'] not in (1, -1):
        sort['direction'] = SORT_DIRECTION_DEFAULT

    runs = db.run.find(skip=(page['page']-1)*page['rows'], limit=page['rows']).sort(sort['by'], sort['direction'])
    return render_template("index.html", runs=runs, page=page, sort=sort)


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
