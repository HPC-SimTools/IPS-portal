from flask import Blueprint, jsonify, request, Response
from typing import Tuple
from . db import db

bp = Blueprint('data', __name__)


@bp.route('/api/data/runs')
def data_runs() -> Tuple[Response, int]:
    runs = []

    for run in db.data.find(projection={'_id': False, "portal_runid": True}):
        runs.append(run['portal_runid'])

    return jsonify(runs), 200


@bp.route('/api/data/<string:portal_runid>')
def data(portal_runid: str) -> Tuple[Response, int]:
    return jsonify(db.data.find_one({"portal_runid": portal_runid}, projection={'_id': False})), 200


@bp.route('/api/data/<string:portal_runid>/tags')
def tags(portal_runid: str) -> Tuple[Response, int]:
    return jsonify(db.data.find_one({"portal_runid": portal_runid},
                                    projection={'_id': False, 'tags': True})['tags']), 200


@bp.route('/api/data/<string:portal_runid>/<string:tag>')
def tagx(portal_runid: str, tag: str) -> Tuple[Response, int]:
    return jsonify(db.data.find_one({"portal_runid": portal_runid},
                                    projection={'_id': False, f'data.{tag}': True})['data'][tag]), 200


@bp.route('/api/data/<string:portal_runid>/<string:tag>/parameters')
def parameters(portal_runid: str, tag: str) -> Tuple[Response, int]:
    return jsonify(list(db.data.find_one({"portal_runid": portal_runid},
                                         projection={'_id': False, f'data.{tag}': True})['data'][tag].keys())), 200


@bp.route('/api/data/<string:portal_runid>/<string:timestamp>/<string:parameter>')
def parameter(portal_runid: str, timestamp: str, parameter: str) -> Tuple[Response, int]:
    return jsonify(db.data.find_one(
        {"portal_runid": portal_runid},
        projection={'_id': False,
                    f'data.{timestamp}.{parameter}': True})['data'][timestamp][parameter]), 200


@bp.route('/api/data', methods=['POST'])
def add() -> Tuple[Response, int]:
    for data in request.get_json():  # type: ignore[attr-defined]
        print(data)

        db.data.update_one({"portal_runid": data['portal_runid']},
                           {
                               "$push": {"tags": data['tag']},
                               "$set": {f"data.{data['tag']}": data['data']}
                           },
                           upsert=True
                           )

    return jsonify("success"), 200


@bp.route('/api/data/query', methods=['POST'])
def query() -> Tuple[Response, int]:
    return jsonify(sorted(x['portal_runid']
                          for x in db.data.find(request.get_json(),  # type: ignore[attr-defined]
                                                projection={'_id': False, "portal_runid": True}))), 200
