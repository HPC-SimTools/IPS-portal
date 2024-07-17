from __future__ import annotations

import logging
from flask import Blueprint, jsonify, request, Response
from typing import Any, Tuple
from .db import db, get_runid, get_data_tags
from .minio import put_minio_object

logger = logging.getLogger(__name__)

bp = Blueprint("data", __name__)


@bp.route("/api/data/runs")
def data_runs() -> Tuple[Response, int]:
    runs = [
        run["portal_runid"]
        for run in db.data.find(projection={"_id": False, "portal_runid": True})
    ]
    return jsonify(runs), 200


@bp.route("/api/data/<string:portal_runid>")
def data(portal_runid: str) -> Tuple[Response, int]:
    result = db.data.find_one({"portal_runid": portal_runid}, projection={"_id": False})
    if result:
        return jsonify(result), 200
    return jsonify("Not Found"), 404


@bp.route("/api/data/<string:portal_runid>/tags")
def tags(portal_runid: str) -> Tuple[Response, int]:
    result = get_data_tags(portal_runid)
    if result:
        return jsonify(result), 200
    return jsonify("Not Found"), 404


@bp.route("/api/data/<string:portal_runid>/<string:tag>")
def tagx(portal_runid: str, tag: str) -> Tuple[Response, int]:
    result: dict[str, Any] | None = db.data.find_one(
        {"portal_runid": portal_runid}, projection={"_id": False, f"data.{tag}": True}
    )
    if result:
        result = result.get("data")
        if result:
            result = result.get(tag)
            if result:
                return jsonify(result), 200
    return jsonify("Not Found"), 404


@bp.route("/api/data/<string:portal_runid>/<string:tag>/parameters")
def parameters(portal_runid: str, tag: str) -> Tuple[Response, int]:
    result: dict[str, Any] | None = db.data.find_one(
        {"portal_runid": portal_runid}, projection={"_id": False, f"data.{tag}": True}
    )
    if result:
        result = result.get("data")
        if result:
            result = result.get(tag)
            if result:
                return jsonify(list(result.keys())), 200
    return jsonify("Not Found"), 404


@bp.route("/api/data/<string:portal_runid>/<string:timestamp>/<string:parameter>")
def parameter(
    portal_runid: str, timestamp: str, parameter: str
) -> Tuple[Response, int]:
    result: dict[str, Any] | None = db.data.find_one(
        {"portal_runid": portal_runid},
        projection={"_id": False, f"data.{timestamp}.{parameter}": True},
    )

    if result:
        result = result.get("data")
        if result:
            result = result.get(timestamp)
            if result:
                result = result.get(parameter)
                if result:
                    return jsonify(result), 200
    return jsonify("Not Found"), 404


@bp.route("/api/data", methods=["POST"])
def add() -> Tuple[Response, int]:
    """
    This is the main POST endpoint for data.

    Metadata should be stored in HTTP Headers, which in turn gets stored in Mongo.
    The raw data itself is the payload (Content-Type is application/octet-stream), and will be stored in MINIO.

    The return value will be an array of data URL locations (JSONified). The response codes are:
    - 500 - adding something to MINIO/Mongo screwed up
    - 400 - missing some important metadata in the headers
    - 201 - all went well, created
    """

    if not request.data:
        return jsonify("Missing request body"), 400

    tag = request.headers.get("X-Ips-Tag")
    if not tag:
        return jsonify("Missing value for HTTP Header X-Ips-Tag"), 400

    portal_runid = request.headers.get("X-Ips-Portal-Runid")
    if not portal_runid:
        return jsonify("Missing value for HTTP Header X-Ips-Portal-Runid"), 400

    # Jupyter links are optional to associate with a data event.
    # If they DO exist, we use a non-printable delimiter to separate links in the header value
    juypter_links_header = request.headers.get("X-Ips-Jupyter-Links")
    if juypter_links_header:
        jupyter_links = juypter_links_header.split("\x01")
    else:
        jupyter_links = []

    # runid is needed because the portal_runid is not a valid bucket name for MINIO
    runid = get_runid(portal_runid)
    if runid is None:
        # should never really see this because we should already have the IPS-Start event saved at this point
        return jsonify("Invalid value for HTTP Header X-Ips-Portal-Runid"), 400
    # MINIO does not allow for buckets smaller than 3 characters
    runid_str = str(runid).zfill(3)

    # TODO allow for portal to specify MIME type (note that this will differ from the HTTP header "Content-Type")
    content_type = "application/octet-stream"

    data_location_url = put_minio_object(
        request.data, bucket_name=runid_str, object_id=tag, content_type=content_type
    )
    if not data_location_url:
        return jsonify("Server could not upload data"), 500

    # try to store tags as floating point value if possible, store as string if not
    try:
        resolved_tag = float(tag)
    except ValueError:
        resolved_tag = tag  # type: ignore

    db.data.update_one(
        {"portal_runid": portal_runid, "runid": runid},
        {
            "$push": {
                "tags": {
                    "tag": resolved_tag,
                    "data_location_url": data_location_url,
                    "jupyter_urls": jupyter_links,
                }
            },
        },
        upsert=True,
    )
    return jsonify(data_location_url), 201


@bp.route("/api/data/add_url", methods=["PUT"])
def add_url() -> Tuple[Response, int]:
    """
    PUT Jupyter URL links

    Response body should be JSON, i.e.
    {
      "url": "https://jupyterlink.com",
      "tags": [
        "1.1231",
        "2324.124"
      ]
    }

    The return value will be an array of data URL locations (JSONified). The response codes are:
    - 200 - created
    - 400 - portal_runid didn't exist, or structure of data was wrong
    - 500 - server error
    """

    data = request.get_json()  # type: ignore[attr-defined]
    errors = []
    url = data.get('url')
    if not isinstance(url, str):
        errors.append({"url": "Must be provided and a string"})

    if not isinstance(data.get('tags'), list):
        errors.append({"tags": "Must be provided and a non-empty list"})
    else:
        try:
            tag_lookups = set(map(float, data.get('tags')))
        except ValueError:
            errors.append({"tags": "Must be floating point values"})

    portal_runid = data.get('portal_runid')
    if not isinstance(portal_runid, str):
        errors.append({"portal_runid": "Must be provided"})
    else:
        result = db.data.find_one(
            {"portal_runid": portal_runid},
        )
        if not result:
            errors.append({"portal_runid": f"{portal_runid} does not exist"})

    if errors:
        return jsonify(errors), 400

    # TODO figure out how to do this entirely in Mongo
    for tags_prop in result['tags']:  # type: ignore[index]
        if tags_prop['tag'] in tag_lookups and url not in tags_prop['jupyter_urls']:
            tags_prop['jupyter_urls'].append(url)
    db.data.replace_one(
        {'_id': result['_id']},  # type: ignore[index]
        result  # type: ignore[arg-type]
    )

    return jsonify([]), 200


@bp.route("/api/data/query", methods=["POST"])
def query() -> Tuple[Response, int]:
    return (
        jsonify(
            sorted(
                x["portal_runid"]
                for x in db.data.find(
                    request.get_json(), projection={"_id": False, "portal_runid": True}  # type: ignore[attr-defined]
                )
            )
        ),
        200,
    )
