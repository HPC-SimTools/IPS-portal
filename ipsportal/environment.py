"""This file is meant to contain all environment-configurable variables."""

import logging
import os
from pathlib import Path

from urllib3.util import parse_url

# LOGGING CONFIG
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)

############ MongoDB config #############################
MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.environ.get('MONGO_PORT', '27017'))
MONGO_USERNAME = os.environ.get('MONGO_USERNAME')
MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD')

################### MinIO config ############################
MINIO_PRIVATE_URL = os.environ.get('MINIO_PRIVATE_URL', 'http://localhost:9000')
"""
This is the URL the backend uses. It must NOT contain a path in the URI.
"""
# check URI
MINIO_URI = parse_url(MINIO_PRIVATE_URL)
if not MINIO_URI.host:
    err_msg = f'MINIO_PRIVATE_URL: Cannot parse host of {MINIO_PRIVATE_URL} (did you include the scheme?)'
    raise RuntimeError(err_msg)

MINIO_PUBLIC_URL = os.environ.get('MINIO_PUBLIC_URL', MINIO_PRIVATE_URL)
"""
This is the URL we expose directly to end users. Paths are allowed here.
"""

MINIO_ROOT_USER = (os.environ.get('MINIO_ROOT_USER', 'AKIAIOSFODNN7EXAMPLE'),)
MINIO_ROOT_PASSWORD = (os.environ.get('MINIO_ROOT_PASSWORD', 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'),)

################## Jaeger config

JAEGER_HOST = os.environ.get('JAEGER_HOST', 'localhost')

################## API authorization config ########################
SECRET_API_KEY = os.environ.get('SECRET_API_KEY', 'changeme')
"""
Primitive mechanism for authorization with the API.

It is currently only used for requests which may change the state of the database.
GET endpoints are currently not authenticated.

This value can be shared with anyone wanting to track their IPS Framework runs.
"""
if SECRET_API_KEY == 'changeme':  # noqa: S105 (checking for the hardcoded value is the point)
    logger.warning('SECRET_API_KEY variable was not set, be sure to change this in production deployments')

SECRET_FLASK_KEY = os.environ.get('SECRET_FLASK_KEY', 'dev')


############# Jupyter shared file mount config ###########################
def get_default_tmp_directory(env_variable_warning_name: str = '') -> Path:
    # used for development
    import tempfile

    if env_variable_warning_name:
        logger.warning(
            '%s is pointing to the default tmp path, be sure you set this in production.', env_variable_warning_name
        )

    return Path(tempfile.gettempdir()) / 'ipsportal-jupyterhub'


JUPYTERHUB_PORTAL_DIR = Path(os.environ.get('JUPYTERHUB_PORTAL_DIR', get_default_tmp_directory()))
"""
This is the path to the shared volume from the WEB PORTAL's perspective.

This should be an absolute path.
"""
if not os.path.isabs(JUPYTERHUB_PORTAL_DIR):
    err_msg = f'JUPYTERHUB_PORTAL_DIR value "{JUPYTERHUB_PORTAL_DIR}" is invalid; it should be an absolute path and should allow creation of a directory.'
    raise RuntimeError(err_msg)
# attempt to create the shared jupyter directory immediately
try:
    os.makedirs(JUPYTERHUB_PORTAL_DIR, exist_ok=True)
except OSError as e:
    err_msg = f'JUPYTERHUB_PORTAL_DIR value "{JUPYTERHUB_PORTAL_DIR}" is invalid; it should be an absolute path and should allow creation of a directory.'
    raise RuntimeError(err_msg) from e

JUPYTERHUB_DIR = Path(os.environ.get('JUPYTERHUB_DIR', '')) or Path(get_default_tmp_directory('JUPYTERHUB_DIR'))
"""
This is the path to the shared volume from the JUPYTERHUB instance's perspective. This is generally used for crafting external URLs to the source.

This should be an absolute path.
"""
if not os.path.isabs(JUPYTERHUB_DIR):
    err_msg = f'JUPYTERHUB_DIR value "{JUPYTERHUB_DIR}" is invalid; it should be an absolute path.'
    raise RuntimeError(err_msg)

JUPYTERHUB_BASE_URL = os.environ.get('JUPYTERHUB_BASE_URL', '')
"""
The base URL of your JupyterHub domain, use for generic implementations. Currently not needed for NERSC.
"""
JUPYTERHUB_IMPLEMENTATION = os.environ.get('JUPYTERHUB_IMPLEMENTATION', 'generic').lower()
"""
set to 'generic' or 'nersc' (by default 'generic')
"""
