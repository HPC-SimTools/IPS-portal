import time
from flask import Blueprint, jsonify, request
import pymongo
from ipsportal.db import get_db

bp = Blueprint('api', __name__)


"""
api/runs GET page? per_page?
api/event POST
api/events/portal_runid GET
api/events/run GET
api/traces/portal_runid GET

api/runs page/per_page
api/run/<number>
api/run/<portal_runid>
api/run/<portal_runid>/events
api/run/<portal_runid>/trace

api/event return runid must exist in run table

"""


@bp.route("/api/runs")
def runs():
    db = get_db()
    runs = db.run.find(projection={'_id': False, 'events': False})
    return jsonify(list(runs))


@bp.route("/api/run/<int:runid>/events")
def events_runid(runid):
    db = get_db()
    r = db.run.find_one({'runid': runid}, projection={"portal_runid": True})
    if r is None:
        return jsonify(message="not found"), 404

    return events(portal_runid=r['portal_runid'])


@bp.route("/api/run/<string:portal_runid>")
def run(portal_runid):
    db = get_db()
    run = db.run.find_one({'portal_runid': portal_runid}, projection={'_id': False})
    return jsonify(run)


@bp.route("/api/run/<string:portal_runid>/events")
def events(portal_runid):
    db = get_db()
    events = db.event.find({'portal_runid': portal_runid},
                           projection={'_id': False, 'trace': False}).sort('seqnum', pymongo.DESCENDING)
    return jsonify(list(events))


@bp.route("/api/run/<string:portal_runid>/trace")
def trace(portal_runid):
    db = get_db()
    traces = db.event.find({'portal_runid': portal_runid}, projection={'trace': True, '_id': False})
    return jsonify([t['trace'] for t in traces if 'trace' in t])


@bp.route("/api/event", methods=['POST'])
def event():
    e = request.json

    required = {'code', 'eventtype', 'comment', 'walltime', 'phystimestamp', 'portal_runid', 'seqnum'}
    if not e.keys() >= required:
        return jsonify(message='Invalid data'), 400

    e['created'] = time.strftime('%Y-%m-%d|%H:%M:%S%Z', time.localtime())

    db = get_db()

    return_data = {}

    if e.get('eventtype') == "IPS_START":
        runid = db.run.count_documents({})
        e['runid'] = runid
        try:
            db.run.insert_one(e)
        except pymongo.errors.DuplicateKeyError:
            return jsonify(message="Duplicate Key"), 400
        return_data['runid'] = runid
    elif e.get('eventtype') == "IPS_END":
        db.run.update_one({'portal_runid': e.get('portal_runid')}, {'$set': e})

    db.event.insert_one(e)

    return_data['message'] = 'success'

    return jsonify(return_data)
