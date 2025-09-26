from __future__ import annotations

import logging
import os
import re

from flask import Blueprint, Response, jsonify, request
from pymongo.errors import PyMongoError

from .db import db
from .environment import SECRET_API_KEY
from .jupyter import add_analysis_data_file_for_timestep, add_ensemble_file, add_jupyter_notebook
from .util import is_valid_filename

logger = logging.getLogger(__name__)

VALID_USERNAME_REGEX = re.compile('^[a-z0-9_]+$')
"""This is the username regex on NERSC, and is probably a good one to use in general."""

bp = Blueprint('data', __name__)


@bp.route('/api/data/runs')
def data_runs() -> tuple[Response, int]:
    runs = [run['portal_runid'] for run in db.data.find(projection={'_id': False, 'portal_runid': True})]
    return jsonify(runs), 200


@bp.route('/api/data/<string:portal_runid>')
def data(portal_runid: str) -> tuple[Response, int]:
    result = db.data.find_one({'portal_runid': portal_runid}, projection={'_id': False})
    if result:
        return jsonify(result), 200
    return jsonify('Not Found'), 404


'''
@bp.route("/api/data", methods=["POST"])
def add() -> tuple[Response, int]:
    """
    This is the main POST endpoint for data.

    Metadata should be stored in HTTP Headers, which in turn gets stored in Mongo.
    The raw data itself is the payload (Content-Type is application/octet-stream), and will be stored in MINIO.

    The return value will be an array of data URL locations (JSONified). The response codes are:
    - 500 - adding something to MINIO/Mongo screwed up
    - 401 - unauthorized
    - 400 - missing some important metadata in the headers
    - 201 - all went well, created
    """

    api_key = request.headers.get("X-Api-Key")
    if api_key != SECRET_API_KEY:
        return jsonify(message="Authorization failed"), 401

    if not request.data:
        return jsonify("Missing request body"), 400

    tag = request.headers.get("X-Ips-Tag")
    if not tag:
        return jsonify("Missing value for HTTP Header X-Ips-Tag"), 400

    portal_runid = request.headers.get("X-Ips-Portal-Runid")
    if not portal_runid:
        return jsonify("Missing value for HTTP Header X-Ips-Portal-Runid"), 400

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

    try:
        db.data.update_one(
            {"portal_runid": portal_runid, "runid": runid},
            {
                "$push": {
                    "tags": {
                        "tag": resolved_tag,
                        "data_location_url": data_location_url,
                    }
                },
            },
            upsert=True,
        )
        return jsonify(data_location_url), 201
    except PyMongoError as e:
        print(e)
        return jsonify('unable to fully link data', e), 500
'''


@bp.route('/api/data/add_notebook', methods=['POST'])
def add_notebook() -> tuple[Response, int]:
    """
    Add a JupyterHub Notebook

    Required Parameters:
    - X-Api-Key - auth
    - X-Ips-Username - username
    - X-Ips-Filename - name of file we want to add (no directories)
    - X-Ips-Portal-Runid - portal runid, this must already exist

    request body = the notebook itself, in bytes

    The return value will be an array of data URL locations (JSONified). The response codes are:
    - 500 - server screwed up
    - 401 - unauthorized
    - 400 - missing some important metadata in the headers, or parameter validation error
    - 201 - all went well, created
    """

    # TODO: later on need to implement real Authentication/Authorization
    api_key = request.headers.get('X-Api-Key')
    if api_key != SECRET_API_KEY:
        return jsonify(message='Authorization failed'), 401

    if request.headers.get('Content-Type') != 'application/octet-stream':
        return jsonify("Content-Type HTTP header value must be 'application/octet-stream'"), 415

    username = request.headers.get('X-Ips-Username')
    if not username:
        return jsonify('Missing value for HTTP Header X-Ips-Username'), 400
    if not VALID_USERNAME_REGEX.match(username):
        return jsonify('Invalid username'), 400

    filename = request.headers.get('X-Ips-Filename')
    if not filename:
        return jsonify('Missing value for HTTP Header X-Ips-Filename'), 400
    filename = os.path.basename(filename)
    if not filename or not filename.endswith('.ipynb'):
        return jsonify('Invalid jupyter notebook filename'), 400
    if not is_valid_filename(filename[:-6]):
        logger.warning('Invalid filename %s, ascii characters [%s]', filename, ', '.join(str(ord(i)) for i in filename))
        return jsonify('Invalid jupyter notebook filename'), 400

    if not request.data:
        return jsonify('Missing request body'), 400

    portal_runid = request.headers.get('X-Ips-Portal-Runid')
    if not portal_runid:
        return jsonify('Missing value for HTTP Header X-Ips-Portal-Runid'), 400

    # TODO fix this block
    try:
        runid = int(portal_runid)
    except ValueError:
        return jsonify('Invalid value for HTTP Header X-Ips-Portal-Runid'), 400
    # runid = get_runid(portal_runid)
    # print('portal_runid', portal_runid, 'runid', runid)
    # if runid is None:
    # should never really see this because we should already have the IPS-Start event saved at this point
    # return jsonify("Invalid value for HTTP Header X-Ips-Portal-Runid"), 400

    result = add_jupyter_notebook(runid, username, filename, request.data)

    if result[1] < 400:
        try:
            db.data.update_one(
                {'runid': runid},
                {
                    '$push': {
                        'jupyter_urls': result[0],
                    },
                },
                upsert=True,
            )
        except PyMongoError:
            logger.exception('unable to add URL when adding notebook')
            return jsonify('unable to add URL but did add notebook'), 500
    return jsonify(result[0]), result[1]


@bp.route('/api/data/add_data_file', methods=['POST'])
def add_data_file() -> tuple[Response, int]:
    """
    Add a data file to the filesystem and the module file.

    Required Parameters:
    - X-Api-Key - auth
    - X-Ips-Username - username
    - X-Ips-Filename - name of file we want to add (no directories)
    - X-Ips-Tag - timestep
    - X-Ips-Portal-Runid - portal runid, this must already exist

    request body = the data file itself, in bytes

    Optional Parameters:
    - X-Ips-Replace - leave value empty if additive, remove if replacing

    The return value will be an array of data URL locations (JSONified). The response codes are:
    - 500 - server screwed up
    - 401 - unauthorized
    - 400 - missing some important metadata in the headers, or parameter validation error
    - 201 - all went well, created
    """

    # TODO: later on need to implement real Authentication/Authorization
    api_key = request.headers.get('X-Api-Key')
    if api_key != SECRET_API_KEY:
        return jsonify(message='Authorization failed'), 401

    if request.headers.get('Content-Type') != 'application/octet-stream':
        return jsonify("Content-Type HTTP header value must be 'application/octet-stream'"), 415

    username = request.headers.get('X-Ips-Username')
    if not username:
        return jsonify('Missing value for HTTP Header X-Ips-Username'), 400
    if not VALID_USERNAME_REGEX.match(username):
        return jsonify('Invalid username'), 400

    filename = request.headers.get('X-Ips-Filename')
    if not filename:
        return jsonify('Missing value for HTTP Header X-Ips-Filename'), 400
    filename = os.path.basename(filename)
    if not filename:
        return jsonify('Invalid filename'), 400
    if not is_valid_filename(filename):
        logger.warning('Invalid filename %s, ascii characters [%s]', filename, ', '.join(str(ord(i)) for i in filename))
        return jsonify('Invalid filename, only alphanumerics, dot, hyphen, underscore, and %+# allowed'), 400

    if not request.data:
        return jsonify('Missing request body'), 400

    tag = request.headers.get('X-Ips-Tag')
    if not tag:
        return jsonify('Missing value for HTTP Header X-Ips-Tag'), 400
    try:
        timestep = float(tag)  # type: ignore[assignment]
    except ValueError:
        return jsonify('Invalid value for HTTP Header X-Ips-Tag'), 400

    replace = bool(request.headers.get('X-Ips-Replace'))

    portal_runid = request.headers.get('X-Ips-Portal-Runid')
    if not portal_runid:
        return jsonify('Missing value for HTTP Header X-Ips-Portal-Runid'), 400

    try:
        runid = int(portal_runid)
    except ValueError:
        return jsonify('Invalid value for HTTP Header X-Ips-Portal-Runid'), 400

    archive_format = request.headers.get('X-Ips-Archive-Format', '')

    result = add_analysis_data_file_for_timestep(
        runid, username, filename, request.data, timestep, replace, archive_format
    )
    return jsonify(result[0]), result[1]


@bp.route('/api/data/add_ensemble_variables', methods=['POST'])
def add_ensemble_variables() -> tuple[Response, int]:
    """
    Add a data file to the filesystem and the module file.

    Required Parameters:
    - X-Api-Key - auth
    - X-Ips-Username - username
    - X-Ips-Portal-Runid - portal runid, this must already exist
    - X-Ips-Ensemble-Id - ID associated with a specific ensemble run (all ensemble children should post this)
    - X-Ips-Sim-Name - the name of the simulation

    request body = the data file itself, in bytes

    Optional Parameters:
    - X-Ips-Replace - leave value empty if additive, remove if replacing

    The return value will be an array of data URL locations (JSONified). The response codes are:
    - 500 - server screwed up
    - 401 - unauthorized
    - 400 - missing some important metadata in the headers, or parameter validation error
    - 201 - all went well, created
    """
    # TODO: later on need to implement real Authentication/Authorization
    api_key = request.headers.get('X-Api-Key')
    if api_key != SECRET_API_KEY:
        return jsonify(message='Authorization failed'), 401

    if request.headers.get('Content-Type') != 'text/csv':
        return jsonify("Content-Type HTTP header value must be 'text/csv'"), 415

    username = request.headers.get('X-Ips-Username')
    if not username:
        return jsonify('Missing value for HTTP Header X-Ips-Username'), 400
    if not VALID_USERNAME_REGEX.match(username):
        return jsonify('Invalid username'), 400

    portal_runid = request.headers.get('X-Ips-Portal-Runid')
    if not portal_runid:
        return jsonify('Missing value for HTTP Header X-Ips-Portal-Runid'), 400

    try:
        runid = int(portal_runid)
    except ValueError:
        return jsonify('Invalid value for HTTP Header X-Ips-Portal-Runid'), 400

    ensemble_id = request.headers.get('X-Ips-Ensemble-Id')
    if not ensemble_id:
        return jsonify('Missing value for HTTP Header X-Ips-Ensemble-Id'), 400

    ensemble_name = request.headers.get('X-Ips-Ensemble-Name')
    if not ensemble_name:
        return jsonify('Missing value for HTTP Header X-Ips-Ensemble-Name'), 400

    result = add_ensemble_file(
        runid,
        username,
        ensemble_name,
        ensemble_id,
        request.data,
    )
    return jsonify(result[0]), result[1]
