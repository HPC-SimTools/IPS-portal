from __future__ import annotations

import logging
from flask import Blueprint, jsonify, request, Response
from typing import Any, Tuple
from . db import db

logger = logging.getLogger(__name__)

bp = Blueprint('data', __name__)


@bp.route('/api/data/runs')
def data_runs() -> Tuple[Response, int]:
    runs = []

    for run in db.data.find(projection={'_id': False, "portal_runid": True}):
        runs.append(run['portal_runid'])

    return jsonify(runs), 200


@bp.route('/api/data/<string:portal_runid>')
def data(portal_runid: str) -> Tuple[Response, int]:
    result = db.data.find_one({"portal_runid": portal_runid}, projection={'_id': False})
    if result:
        return jsonify(result), 200
    return jsonify('Not Found'), 404


@bp.route('/api/data/<string:portal_runid>/tags')
def tags(portal_runid: str) -> Tuple[Response, int]:
    result = db.data.find_one(
        {"portal_runid": portal_runid},
        projection={'_id': False, 'tags': True}
    )
    if result:
        result = result.get('tags')
        if result:
            return jsonify(result), 200
    return jsonify('Not Found'), 404


@bp.route('/api/data/<string:portal_runid>/<string:tag>')
def tagx(portal_runid: str, tag: str) -> Tuple[Response, int]:
    result: dict[str, Any] | None = db.data.find_one(
        {"portal_runid": portal_runid},
        projection={'_id': False, f'data.{tag}': True}
    )
    if result:
        result = result.get('data')
        if result:
            result = result.get(tag)
            if result:
                return jsonify(result), 200
    return jsonify('Not Found'), 404


@bp.route('/api/data/<string:portal_runid>/<string:tag>/parameters')
def parameters(portal_runid: str, tag: str) -> Tuple[Response, int]:
    result: dict[str, Any] | None = db.data.find_one(
        {"portal_runid": portal_runid},
        projection={'_id': False, f'data.{tag}': True}
    )
    if result:
        result = result.get('data')
        if result:
            result = result.get(tag)
            if result:
                return jsonify(list(result.keys())), 200
    return jsonify('Not Found'), 404


@bp.route('/api/data/<string:portal_runid>/<string:timestamp>/<string:parameter>')
def parameter(portal_runid: str, timestamp: str, parameter: str) -> Tuple[Response, int]:
    result: dict[str, Any] | None = db.data.find_one(
        {"portal_runid": portal_runid},
        projection={'_id': False,
                    f'data.{timestamp}.{parameter}': True})

    if result:
        result = result.get('data')
        if result:
            result = result.get(timestamp)
            if result:
                result = result.get(parameter)
                if result:
                    return jsonify(result), 200
    return jsonify('Not Found'), 404


@bp.route('/api/data', methods=['POST'])
def add() -> Tuple[Response, int]:
    for data in request.get_json():
        logger.info(data)

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
                          for x in db.data.find(request.get_json(),
                                                projection={'_id': False, "portal_runid": True}))), 200
